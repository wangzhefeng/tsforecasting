"""普通预测流程的 YAML 配置类型、构建、校验与 CLI override 解析。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tsforecasting.config.common import (
    VALID_LOG_LEVELS,
    ArtifactsConfig,
    ConfigError,
    RuntimeConfig,
    apply_run_overrides,
    build_runtime,
    load_yaml_mapping,
    require,
    require_pos_int,
    require_str,
)

SUPPORTED_BACKENDS = frozenset({"statsforecast", "mlforecast", "neuralforecast"})
CORE_METRICS = frozenset({"mae", "rmse", "mape", "smape"})
_TOP_LEVEL_KEYS = frozenset(
    {
        "version",
        "task",
        "data",
        "split",
        "models",
        "evaluation",
        "forecast",
        "prediction_intervals",
        "runtime",
        "output",
        "seed",
    }
)


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
class ForecastConfig:
    horizon: int


@dataclass
class MLForecastConfig:
    """MLForecast 后端共享的 lag、日期特征和目标变换配置。"""

    lags: list[int]
    date_features: list[str] | None = None
    target_transforms: list[dict[str, Any]] | None = None


@dataclass
class PredictionIntervalsConfig:
    """可选预测区间配置；levels 对应输出列 lo-{level}/hi-{level}。"""

    levels: list[int]


@dataclass
class OutputConfig:
    dir: str
    save_plots: bool = False


@dataclass
class ForecastArgs:
    data: DataConfig
    split: BacktestConfig
    models: list[ModelConfig]
    evaluation: EvaluationConfig
    runtime: RuntimeConfig
    output: OutputConfig
    forecast: ForecastConfig | None = None
    version: int = 2
    task: str = "forecast"
    seed: int = 0
    mlforecast: MLForecastConfig | None = None
    prediction_intervals: PredictionIntervalsConfig | None = None
    run_id: str | None = None
    config_source: str | None = None

    @property
    def backtest(self) -> BacktestConfig:
        """兼容旧内部命名；新 YAML 中该 section 叫 split。"""
        return self.split

    @property
    def predict(self) -> ForecastConfig | None:
        """兼容旧内部命名；新 YAML 中该 section 叫 forecast。"""
        return self.forecast

    @property
    def artifacts(self) -> ArtifactsConfig:
        """兼容旧代码读取，实际来源是 output section。"""
        return ArtifactsConfig(
            output_dir=self.output.dir, save_plots=self.output.save_plots
        )


# 旧内部类型名保留为别名，迁移期内 registry/adapter 不需要关心重命名。
Config = ForecastArgs
PredictConfig = ForecastConfig


def _ensure_no_unknown_keys(raw: dict) -> None:
    unknown = sorted(set(raw) - _TOP_LEVEL_KEYS)
    if unknown:
        raise ConfigError(f"unknown top-level config keys: {unknown}")


def _build_data(raw: dict) -> DataConfig:
    """构建 data section；这里只校验字段类型，不读取真实数据文件。"""
    path = require_str(raw, "path", "data")
    time_col = require_str(raw, "time_col", "data")
    target_col = require_str(raw, "target_col", "data")
    id_col = raw.get("id_col")
    if id_col is not None and not isinstance(id_col, str):
        raise ConfigError("data: 'id_col' must be a string or null")
    freq = raw.get("freq")
    if freq is not None and (not isinstance(freq, str) or not freq.strip()):
        raise ConfigError("data: 'freq' must be a non-empty string or null")
    return DataConfig(
        path=path, time_col=time_col, target_col=target_col, id_col=id_col, freq=freq
    )


def _build_model_list(raw: Any, backend: str) -> list[ModelConfig]:
    if not isinstance(raw, list) or not raw:
        raise ConfigError(f"models.{backend}: must be a non-empty list")
    out: list[ModelConfig] = []
    for i, m in enumerate(raw):
        if not isinstance(m, dict):
            raise ConfigError(f"models.{backend}[{i}]: must be a mapping")
        name = require_str(m, "name", f"models.{backend}[{i}]")
        params = m.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"models.{backend}[{i}].params: must be a mapping")
        out.append(ModelConfig(name=name, backend=backend, params=dict(params)))
    return out


def _build_mlforecast(raw: dict) -> MLForecastConfig:
    """构建 MLForecast 共享配置，保持 target_transforms 为 YAML 可序列化 spec。"""
    lags = require(raw, "lags", "models.mlforecast.framework")
    if not isinstance(lags, list) or not lags or not all(
        isinstance(x, int) and not isinstance(x, bool) for x in lags
    ):
        raise ConfigError("models.mlforecast.framework.lags: must be a non-empty list of integers")
    date_features = raw.get("date_features")
    if date_features is not None and (
        not isinstance(date_features, list)
        or not all(isinstance(x, str) for x in date_features)
    ):
        raise ConfigError(
            "models.mlforecast.framework.date_features: must be a list of strings or null"
        )
    target_transforms = raw.get("target_transforms")
    if target_transforms is not None:
        if not isinstance(target_transforms, list):
            raise ConfigError(
                "models.mlforecast.framework.target_transforms: must be a list or null"
            )
        for i, spec in enumerate(target_transforms):
            if (
                not isinstance(spec, dict)
                or not isinstance(spec.get("class"), str)
                or not spec["class"].strip()
            ):
                raise ConfigError(
                    f"models.mlforecast.framework.target_transforms[{i}]: "
                    "must be a mapping with a string 'class'"
                )
            for k in ("args", "kwargs"):
                v = spec.get(k)
                if v is not None and not isinstance(v, (list, dict)):
                    raise ConfigError(
                        f"models.mlforecast.framework.target_transforms[{i}].{k}: "
                        "must be a list/dict or null"
                    )
    return MLForecastConfig(
        lags=list(lags),
        date_features=list(date_features) if date_features else None,
        target_transforms=list(target_transforms) if target_transforms else None,
    )


def _build_models(raw: Any) -> tuple[list[ModelConfig], MLForecastConfig | None]:
    """把 backend 分组模型配置 flatten 成统一 ModelConfig 列表。"""
    if not isinstance(raw, dict) or not raw:
        raise ConfigError("models: must be a non-empty mapping grouped by backend")

    models: list[ModelConfig] = []
    mlforecast: MLForecastConfig | None = None
    for backend, spec in raw.items():
        if backend not in SUPPORTED_BACKENDS:
            raise ConfigError(
                f"models: backend '{backend}' not supported "
                f"(supported: {sorted(SUPPORTED_BACKENDS)})"
            )
        if backend == "mlforecast":
            if not isinstance(spec, dict):
                raise ConfigError("models.mlforecast: must contain framework and models")
            framework = spec.get("framework")
            if not isinstance(framework, dict):
                raise ConfigError("models.mlforecast.framework: must be a mapping")
            mlforecast = _build_mlforecast(framework)
            models.extend(_build_model_list(spec.get("models"), backend))
        else:
            models.extend(_build_model_list(spec, backend))
    if not models:
        raise ConfigError("models: must contain at least one model")
    return models, mlforecast


def _build_evaluation(raw: dict) -> EvaluationConfig:
    metrics = require(raw, "metrics", "evaluation")
    if not isinstance(metrics, list) or not metrics:
        raise ConfigError("evaluation.metrics: must be a non-empty list")
    return EvaluationConfig(metrics=list(metrics), rank_metric=raw.get("rank_metric", "mae"))


def _build_prediction_intervals(raw: dict) -> PredictionIntervalsConfig:
    levels = require(raw, "levels", "prediction_intervals")
    if (
        not isinstance(levels, list)
        or not levels
        or not all(
            isinstance(x, int) and not isinstance(x, bool) and 0 < x < 100
            for x in levels
        )
    ):
        raise ConfigError(
            "prediction_intervals.levels: must be a non-empty list of integers "
            "in (0, 100)"
        )
    return PredictionIntervalsConfig(levels=list(levels))


def _build_output(raw: dict) -> OutputConfig:
    return OutputConfig(
        dir=require_str(raw, "dir", "output"),
        save_plots=bool(raw.get("save_plots", False)),
    )


def _build_config(raw: dict) -> ForecastArgs:
    """把 YAML 根 mapping 转成 ForecastArgs；跨 section 约束交给 validate()。"""
    _ensure_no_unknown_keys(raw)
    version = raw.get("version", 2)
    if version != 2:
        raise ConfigError("version must be 2")
    task = raw.get("task", "forecast")
    if task != "forecast":
        raise ConfigError("task must be 'forecast'")

    data = _build_data(require(raw, "data", "config"))
    split_raw = require(raw, "split", "config")
    split = BacktestConfig(
        horizon=require_pos_int(split_raw, "horizon", "split"),
        n_windows=require_pos_int(split_raw, "n_windows", "split"),
        step_size=require_pos_int(split_raw, "step_size", "split"),
    )
    models, mlforecast = _build_models(require(raw, "models", "config"))
    evaluation = _build_evaluation(require(raw, "evaluation", "config"))
    runtime = build_runtime(raw.get("runtime") or {})
    output = _build_output(require(raw, "output", "config"))
    forecast = None
    if raw.get("forecast"):
        forecast = ForecastConfig(
            horizon=require_pos_int(raw["forecast"], "horizon", "forecast")
        )
    prediction_intervals = None
    if raw.get("prediction_intervals"):
        prediction_intervals = _build_prediction_intervals(raw["prediction_intervals"])
    seed = raw.get("seed", 0)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ConfigError("seed must be an integer")
    return ForecastArgs(
        version=version,
        task=task,
        data=data,
        split=split,
        models=models,
        evaluation=evaluation,
        runtime=runtime,
        output=output,
        forecast=forecast,
        mlforecast=mlforecast,
        prediction_intervals=prediction_intervals,
        seed=seed,
    )


def validate(config: ForecastArgs) -> ForecastArgs:
    """执行跨字段校验；必填项和基础类型校验已在 build 阶段完成。"""
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
            # 只读取 registry 元数据，不 import 可选 backend，也不实例化模型。
            entry = get_entry(m.name)
        except RegistryError as exc:
            raise ConfigError(str(exc)) from exc
        if entry.backend != m.backend:
            raise ConfigError(
                f"model '{m.name}': config backend '{m.backend}' "
                f"!= registry backend '{entry.backend}'"
            )

    if any(m.backend == "mlforecast" for m in config.models) and config.mlforecast is None:
        raise ConfigError(
            "models use backend 'mlforecast' but no models.mlforecast.framework "
            "section is configured"
        )

    bad_metrics = [m for m in config.evaluation.metrics if m not in CORE_METRICS]
    if bad_metrics:
        raise ConfigError(
            f"evaluation.metrics: unsupported {bad_metrics} "
            f"(core: {sorted(CORE_METRICS)})"
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

    if not config.output.dir.strip():
        raise ConfigError("output.dir must be a non-empty string")
    if config.forecast is not None and config.forecast.horizon <= 0:
        raise ConfigError("forecast.horizon must be a positive integer")
    return config


def load_config(path: str | Path) -> ForecastArgs:
    """读取 forecast YAML，并返回已经校验过的 ForecastArgs。"""
    p, raw = load_yaml_mapping(path)
    config = _build_config(raw)
    config.config_source = str(p.resolve())
    return validate(config)


def resolve_overrides(
    config: ForecastArgs,
    *,
    run_id: str | None = None,
    output_dir: str | None = None,
    log_name: str | None = None,
    log_level: str | None = None,
) -> ForecastArgs:
    """应用 CLI 运行级覆盖；覆盖后再次 validate，避免绕过配置校验。"""
    return apply_run_overrides(
        config,
        run_id=run_id,
        output_dir=output_dir,
        log_name=log_name,
        log_level=log_level,
        validate=validate,
    )
