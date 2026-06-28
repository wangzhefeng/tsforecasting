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
    build_artifacts,
    build_runtime,
    load_yaml_mapping,
    require,
    require_pos_int,
    require_str,
)

SUPPORTED_BACKENDS = frozenset({"statsforecast", "mlforecast", "neuralforecast"})
CORE_METRICS = frozenset({"mae", "rmse", "mape", "smape"})


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
    """
    MLForecast 后端共享的 lag、日期特征和目标变换配置。
    """
    lags: list[int]
    date_features: list[str] | None = None
    target_transforms: list[dict[str, Any]] | None = None


@dataclass
class PredictionIntervalsConfig:
    """
    可选预测区间配置；levels 对应输出列 lo-{level}/hi-{level}。
    """
    levels: list[int]


@dataclass
class Config:
    data: DataConfig
    backtest: BacktestConfig
    models: list[ModelConfig]
    evaluation: EvaluationConfig
    runtime: RuntimeConfig
    artifacts: ArtifactsConfig
    predict: PredictConfig | None = None
    seed: int = 0
    mlforecast: MLForecastConfig | None = None
    prediction_intervals: PredictionIntervalsConfig | None = None
    # 运行时解析：来自 CLI override 或默认 run_id 生成。
    run_id: str | None = None
    config_source: str | None = None


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


def _build_models(raw: Any) -> list[ModelConfig]:
    """构建模型列表；模型名和 backend 是否注册在 validate() 阶段校验。"""
    if not isinstance(raw, list) or not raw:
        raise ConfigError("models: must be a non-empty list")
    out: list[ModelConfig] = []
    for i, m in enumerate(raw):
        if not isinstance(m, dict):
            raise ConfigError(f"models[{i}]: must be a mapping")
        name = require_str(m, "name", f"models[{i}]")
        backend = require_str(m, "backend", f"models[{i}]")
        params = m.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"models[{i}]: 'params' must be a mapping")
        out.append(ModelConfig(name=name, backend=backend, params=dict(params)))
    return out


def _build_evaluation(raw: dict) -> EvaluationConfig:
    metrics = require(raw, "metrics", "evaluation")
    if not isinstance(metrics, list) or not metrics:
        raise ConfigError("evaluation.metrics: must be a non-empty list")
    return EvaluationConfig(metrics=list(metrics), rank_metric=raw.get("rank_metric", "mae"))


def _build_mlforecast(raw: dict) -> MLForecastConfig:
    """构建 MLForecast 共享配置，保持 target_transforms 为 YAML 可序列化 spec。"""
    lags = require(raw, "lags", "mlforecast")
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
            if (
                not isinstance(spec, dict)
                or not isinstance(spec.get("class"), str)
                or not spec["class"].strip()
            ):
                raise ConfigError(
                    f"mlforecast.target_transforms[{i}]: must be a mapping "
                    "with a string 'class'"
                )
            for k in ("args", "kwargs"):
                v = spec.get(k)
                if v is not None and not isinstance(v, (list, dict)):
                    raise ConfigError(
                        f"mlforecast.target_transforms[{i}].{k}: "
                        "must be a list/dict or null"
                    )
    return MLForecastConfig(
        lags=list(lags),
        date_features=list(date_features) if date_features else None,
        target_transforms=list(target_transforms) if target_transforms else None,
    )


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


def _build_config(raw: dict) -> Config:
    """把 YAML 根 mapping 转成 Config；跨 section 约束交给 validate()。"""
    data = _build_data(require(raw, "data", "config"))
    bt_raw = require(raw, "backtest", "config")
    backtest = BacktestConfig(
        horizon=require_pos_int(bt_raw, "horizon", "backtest"),
        n_windows=require_pos_int(bt_raw, "n_windows", "backtest"),
        step_size=require_pos_int(bt_raw, "step_size", "backtest"),
    )
    models = _build_models(require(raw, "models", "config"))
    evaluation = _build_evaluation(require(raw, "evaluation", "config"))
    runtime = build_runtime(raw.get("runtime") or {})
    artifacts = build_artifacts(require(raw, "artifacts", "config"))
    predict = None
    if raw.get("predict"):
        predict = PredictConfig(
            horizon=require_pos_int(raw["predict"], "horizon", "predict")
        )
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

    if any(m.backend == "mlforecast" for m in config.models):
        if config.mlforecast is None:
            raise ConfigError(
                "models use backend 'mlforecast' but no top-level 'mlforecast' "
                "section (with non-empty 'lags') is configured"
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
    """
    读取普通 forecast YAML，并返回已经校验过的 Config。
    """
    p, raw = load_yaml_mapping(path)
    config = _build_config(raw)
    config.config_source = str(p.resolve())
    return validate(config)


def resolve_overrides(
    config: Config,
    *,
    run_id: str | None = None,
    output_dir: str | None = None,
    log_name: str | None = None,
    log_level: str | None = None,
) -> Config:
    """应用 CLI 运行级覆盖；覆盖后再次 validate，避免绕过配置校验。"""
    return apply_run_overrides(
        config,
        run_id=run_id,
        output_dir=output_dir,
        log_name=log_name,
        log_level=log_level,
        validate=validate,
    )
