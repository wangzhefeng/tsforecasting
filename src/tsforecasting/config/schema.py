"""YAML configuration schema, validation, and run-id / override resolution.

MVP-0 uses a single YAML file (no Python config, no multi-file merge) plus a
small allow-list of run-level CLI overrides. Validation is stdlib-only
(dataclasses + explicit checks); no pydantic, to keep the base dependency
surface at the Nixtla pair + pyyaml.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_BACKENDS = frozenset({"statsforecast", "mlforecast", "neuralforecast"})
CORE_METRICS = frozenset({"mae", "rmse", "mape", "smape"})
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigError(ValueError):
    """Raised when a config file fails schema validation."""


@dataclass
class DataConfig:
    path: str
    time_col: str
    target_col: str
    id_col: str | None = None
    freq: str | None = None


@dataclass
class BacktestConfig:
    horizon: int
    n_windows: int
    step_size: int


@dataclass
class ModelConfig:
    name: str
    backend: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationConfig:
    metrics: list[str]
    rank_metric: str = "mae"


@dataclass
class PredictConfig:
    horizon: int


@dataclass
class MLForecastConfig:
    """Shared MLForecast framework params (lags / date features / target transforms).

    MLForecast wraps all its inner models in one framework object that shares
    these feature/transform settings, so they live at the top level rather than
    per-model. ``target_transforms`` is a serializable spec (``{class, args?,
    kwargs?}``) resolved by the adapter, keeping ``run_config.yaml`` YAML-safe.
    """

    lags: list[int]
    date_features: list[str] | None = None
    target_transforms: list[dict[str, Any]] | None = None


@dataclass
class PredictionIntervalsConfig:
    """Optional prediction-interval levels (Phase 2). When set, statsforecast
    forecasts/backtests append ``lo-{level}``/``hi-{level}`` columns and the
    evaluator computes coverage/width per level."""

    levels: list[int]


@dataclass
class RuntimeConfig:
    collect_timing: bool = True
    log_name: str = "main"
    log_level: str = "INFO"


@dataclass
class ArtifactsConfig:
    output_dir: str
    save_plots: bool = False


@dataclass
class Config:
    data: DataConfig
    backtest: BacktestConfig
    models: list[ModelConfig]
    evaluation: EvaluationConfig
    runtime: RuntimeConfig
    artifacts: ArtifactsConfig
    predict: PredictConfig | None = None
    mlforecast: MLForecastConfig | None = None
    prediction_intervals: PredictionIntervalsConfig | None = None
    seed: int = 0
    # resolved at run time:
    run_id: str | None = None
    config_source: str | None = None


def _require(mapping: dict, key: str, ctx: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"{ctx}: missing required key '{key}'")
    return mapping[key]


def _require_str(mapping: dict, key: str, ctx: str) -> str:
    val = _require(mapping, key, ctx)
    if not isinstance(val, str) or not val.strip():
        raise ConfigError(f"{ctx}: '{key}' must be a non-empty string")
    return val


def _require_pos_int(mapping: dict, key: str, ctx: str) -> int:
    val = _require(mapping, key, ctx)
    if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
        raise ConfigError(f"{ctx}: '{key}' must be a positive integer")
    return val


def _build_data(raw: dict) -> DataConfig:
    path = _require_str(raw, "path", "data")
    time_col = _require_str(raw, "time_col", "data")
    target_col = _require_str(raw, "target_col", "data")
    id_col = raw.get("id_col")
    if id_col is not None and not isinstance(id_col, str):
        raise ConfigError("data: 'id_col' must be a string or null")
    freq = raw.get("freq")
    if freq is not None and (not isinstance(freq, str) or not freq.strip()):
        raise ConfigError("data: 'freq' must be a non-empty string or null")
    return DataConfig(
        path=path, time_col=time_col, target_col=target_col, id_col=id_col, freq=freq
    )


def _build_models(raw: Any) -> list[ModelConfig]:
    if not isinstance(raw, list) or not raw:
        raise ConfigError("models: must be a non-empty list")
    out: list[ModelConfig] = []
    for i, m in enumerate(raw):
        if not isinstance(m, dict):
            raise ConfigError(f"models[{i}]: must be a mapping")
        name = _require_str(m, "name", f"models[{i}]")
        backend = _require_str(m, "backend", f"models[{i}]")
        params = m.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"models[{i}]: 'params' must be a mapping")
        out.append(ModelConfig(name=name, backend=backend, params=dict(params)))
    return out


def _build_evaluation(raw: dict) -> EvaluationConfig:
    metrics = _require(raw, "metrics", "evaluation")
    if not isinstance(metrics, list) or not metrics:
        raise ConfigError("evaluation.metrics: must be a non-empty list")
    return EvaluationConfig(metrics=list(metrics), rank_metric=raw.get("rank_metric", "mae"))


def _build_runtime(raw: dict) -> RuntimeConfig:
    return RuntimeConfig(
        collect_timing=bool(raw.get("collect_timing", True)),
        log_name=raw.get("log_name", "main"),
        log_level=raw.get("log_level", "INFO"),
    )


def _build_artifacts(raw: dict) -> ArtifactsConfig:
    return ArtifactsConfig(
        output_dir=_require_str(raw, "output_dir", "artifacts"),
        save_plots=bool(raw.get("save_plots", False)),
    )


def _build_mlforecast(raw: dict) -> MLForecastConfig:
    lags = _require(raw, "lags", "mlforecast")
    if not isinstance(lags, list) or not lags or not all(
        isinstance(x, int) and not isinstance(x, bool) for x in lags
    ):
        raise ConfigError("mlforecast.lags: must be a non-empty list of integers")
    date_features = raw.get("date_features")
    if date_features is not None and (
        not isinstance(date_features, list)
        or not all(isinstance(x, str) for x in date_features)
    ):
        raise ConfigError("mlforecast.date_features: must be a list of strings or null")
    target_transforms = raw.get("target_transforms")
    if target_transforms is not None:
        if not isinstance(target_transforms, list):
            raise ConfigError("mlforecast.target_transforms: must be a list or null")
        for i, spec in enumerate(target_transforms):
            if not isinstance(spec, dict) or not isinstance(spec.get("class"), str) or not spec["class"].strip():
                raise ConfigError(
                    f"mlforecast.target_transforms[{i}]: must be a mapping with a string 'class'"
                )
            for k in ("args", "kwargs"):
                v = spec.get(k)
                if v is not None and not isinstance(v, (list, dict)):
                    raise ConfigError(
                        f"mlforecast.target_transforms[{i}].{k}: must be a list/dict or null"
                    )
    return MLForecastConfig(
        lags=list(lags),
        date_features=list(date_features) if date_features else None,
        target_transforms=list(target_transforms) if target_transforms else None,
    )


def _build_prediction_intervals(raw: dict) -> PredictionIntervalsConfig:
    levels = _require(raw, "levels", "prediction_intervals")
    if (
        not isinstance(levels, list)
        or not levels
        or not all(
            isinstance(x, int) and not isinstance(x, bool) and 0 < x < 100 for x in levels
        )
    ):
        raise ConfigError(
            "prediction_intervals.levels: must be a non-empty list of integers in (0, 100)"
        )
    return PredictionIntervalsConfig(levels=list(levels))


def _build_config(raw: dict) -> Config:
    data = _build_data(_require(raw, "data", "config"))
    bt_raw = _require(raw, "backtest", "config")
    backtest = BacktestConfig(
        horizon=_require_pos_int(bt_raw, "horizon", "backtest"),
        n_windows=_require_pos_int(bt_raw, "n_windows", "backtest"),
        step_size=_require_pos_int(bt_raw, "step_size", "backtest"),
    )
    models = _build_models(_require(raw, "models", "config"))
    evaluation = _build_evaluation(_require(raw, "evaluation", "config"))
    runtime = _build_runtime(raw.get("runtime") or {})
    artifacts = _build_artifacts(_require(raw, "artifacts", "config"))
    predict = None
    if raw.get("predict"):
        predict = PredictConfig(horizon=_require_pos_int(raw["predict"], "horizon", "predict"))
    mlforecast = None
    if raw.get("mlforecast"):
        mlforecast = _build_mlforecast(raw["mlforecast"])
    prediction_intervals = None
    if raw.get("prediction_intervals"):
        prediction_intervals = _build_prediction_intervals(raw["prediction_intervals"])
    seed = raw.get("seed", 0)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ConfigError("seed must be an integer")
    return Config(
        data=data,
        backtest=backtest,
        models=models,
        evaluation=evaluation,
        runtime=runtime,
        artifacts=artifacts,
        predict=predict,
        mlforecast=mlforecast,
        prediction_intervals=prediction_intervals,
        seed=seed,
    )


def validate(config: Config) -> Config:
    """Run cross-field validation. Type/required-key checks happen at build time."""
    from tsforecasting.models.registry import RegistryError, get_entry

    names = [m.name for m in config.models]
    if len(set(names)) != len(names):
        raise ConfigError("models: names must be unique")

    for m in config.models:
        if m.backend not in SUPPORTED_BACKENDS:
            raise ConfigError(
                f"models[{m.name}]: backend '{m.backend}' not supported "
                f"(supported: {sorted(SUPPORTED_BACKENDS)})"
            )
        try:
            entry = get_entry(m.name)
        except RegistryError as exc:
            raise ConfigError(str(exc)) from exc
        if entry.backend != m.backend:
            raise ConfigError(
                f"model '{m.name}': config backend '{m.backend}' "
                f"!= registry backend '{entry.backend}'"
            )

    if any(m.backend == "mlforecast" for m in config.models):
        if config.mlforecast is None:
            raise ConfigError(
                "models use backend 'mlforecast' but no top-level 'mlforecast' section "
                "(with non-empty 'lags') is configured"
            )

    bad_metrics = [m for m in config.evaluation.metrics if m not in CORE_METRICS]
    if bad_metrics:
        raise ConfigError(
            f"evaluation.metrics: unsupported {bad_metrics} "
            f"(MVP-0 core: {sorted(CORE_METRICS)})"
        )
    if config.evaluation.rank_metric not in config.evaluation.metrics:
        raise ConfigError(
            f"evaluation.rank_metric '{config.evaluation.rank_metric}' "
            "must be one of evaluation.metrics"
        )

    level = config.runtime.log_level.upper()
    if level not in VALID_LOG_LEVELS:
        raise ConfigError(
            f"runtime.log_level '{config.runtime.log_level}' invalid "
            f"({sorted(VALID_LOG_LEVELS)})"
        )
    config.runtime.log_level = level

    if not config.artifacts.output_dir.strip():
        raise ConfigError("artifacts.output_dir must be a non-empty string")

    if config.predict is not None and config.predict.horizon <= 0:
        raise ConfigError("predict.horizon must be a positive integer")

    return config


def load_config(path: str | Path) -> Config:
    """Load and validate a YAML config file."""
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {path}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")
    config = _build_config(raw)
    config.config_source = str(p.resolve())
    validate(config)
    return config


def generate_run_id() -> str:
    """``tsforecasting-<UTC timestamp YYYYmmddHHMMSS>-<random8>`` (sortable)."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"tsforecasting-{ts}-{secrets.token_hex(4)}"


def resolve_overrides(
    config: Config,
    *,
    run_id: str | None = None,
    output_dir: str | None = None,
    log_name: str | None = None,
    log_level: str | None = None,
) -> Config:
    """Apply run-level CLI overrides in place, defaulting run_id if unset."""
    if run_id is not None:
        config.run_id = run_id
    elif config.run_id is None:
        config.run_id = generate_run_id()
    if output_dir is not None:
        config.artifacts.output_dir = output_dir
    if log_name is not None:
        config.runtime.log_name = log_name
    if log_level is not None:
        config.runtime.log_level = log_level.upper()
    return validate(config)
