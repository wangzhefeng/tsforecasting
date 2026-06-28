"""层级预测协调流程的配置类型、构建、校验与 CLI override 解析。

该配置独立于普通 forecast ``Config``：数据源是 ``datasetsforecast``，
``base_forecast`` 定义基础预测模型，``hierarchical`` 定义 reconciler，
并写出独立的层级 artifact 集合。
"""

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
from tsforecasting.config.forecast import ModelConfig

VALID_HIERARCHICAL_SOURCES = frozenset({"datasetsforecast"})
HIERARCHICAL_BASE_BACKENDS = frozenset({"statsforecast"})
HIERARCHICAL_METRICS = frozenset({"mse"})


@dataclass
class HierarchicalDataConfig:
    source: str
    dataset: str
    freq: str
    cache_dir: str = "dataset/datasetsforecast_cache"


@dataclass
class BaseForecastConfig:
    backend: str
    models: list[ModelConfig]
    horizon: int


@dataclass
class ReconcilerSpec:
    name: str
    class_path: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class HierarchicalEvaluationConfig:
    metrics: list[str]


@dataclass
class HierarchicalSectionConfig:
    reconcilers: list[ReconcilerSpec]
    diagnostics: bool = True


@dataclass
class HierarchicalConfig:
    data: HierarchicalDataConfig
    base_forecast: BaseForecastConfig
    hierarchical: HierarchicalSectionConfig
    evaluation: HierarchicalEvaluationConfig
    runtime: RuntimeConfig
    artifacts: ArtifactsConfig
    seed: int = 0
    # 运行时解析：来自 CLI override 或默认 run_id 生成。
    run_id: str | None = None
    config_source: str | None = None


def _build_hierarchical_data(raw: dict) -> HierarchicalDataConfig:
    """构建层级数据源配置；当前 MVP 只支持 datasetsforecast。"""
    source = require_str(raw, "source", "data")
    if source not in VALID_HIERARCHICAL_SOURCES:
        raise ConfigError(
            f"data.source '{source}' not supported (MVP: {sorted(VALID_HIERARCHICAL_SOURCES)})"
        )
    dataset = require_str(raw, "dataset", "data")
    freq = require_str(raw, "freq", "data")
    cache_dir = raw.get("cache_dir", "dataset/datasetsforecast_cache")
    if not isinstance(cache_dir, str) or not cache_dir.strip():
        raise ConfigError("data.cache_dir must be a non-empty string")
    return HierarchicalDataConfig(
        source=source, dataset=dataset, freq=freq, cache_dir=cache_dir
    )


def _build_base_models(raw: Any, backend: str) -> list[ModelConfig]:
    """构建基础预测模型；backend 来自 base_forecast.backend，不在模型项内重复配置。"""
    if not isinstance(raw, list) or not raw:
        raise ConfigError("base_forecast.models: must be a non-empty list")
    out: list[ModelConfig] = []
    names: set[str] = set()
    for i, m in enumerate(raw):
        if not isinstance(m, dict):
            raise ConfigError(f"base_forecast.models[{i}]: must be a mapping")
        name = require_str(m, "name", f"base_forecast.models[{i}]")
        if name in names:
            raise ConfigError(f"base_forecast.models[{i}]: duplicate name '{name}'")
        names.add(name)
        params = m.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"base_forecast.models[{i}].params: must be a mapping")
        # 层级流程的基础模型共享同一个 backend，避免 YAML 中重复声明。
        out.append(ModelConfig(name=name, backend=backend, params=dict(params)))
    return out


def _build_base_forecast(raw: dict) -> BaseForecastConfig:
    backend = require_str(raw, "backend", "base_forecast")
    if backend not in HIERARCHICAL_BASE_BACKENDS:
        raise ConfigError(
            f"base_forecast.backend '{backend}' not supported "
            f"(MVP: {sorted(HIERARCHICAL_BASE_BACKENDS)})"
        )
    models = _build_base_models(require(raw, "models", "base_forecast"), backend)
    horizon = require_pos_int(raw, "horizon", "base_forecast")
    return BaseForecastConfig(backend=backend, models=models, horizon=horizon)


def _build_reconcilers(raw: Any) -> list[ReconcilerSpec]:
    """构建 reconciler spec；class_path 后续由 resolvers 动态实例化。"""
    if not isinstance(raw, list) or not raw:
        raise ConfigError("hierarchical.reconcilers: must be a non-empty list")
    out: list[ReconcilerSpec] = []
    names: set[str] = set()
    for i, spec in enumerate(raw):
        if not isinstance(spec, dict):
            raise ConfigError(f"hierarchical.reconcilers[{i}]: must be a mapping")
        name = require_str(spec, "name", f"hierarchical.reconcilers[{i}]")
        if name in names:
            raise ConfigError(f"hierarchical.reconcilers[{i}]: duplicate name '{name}'")
        names.add(name)
        class_path = require_str(spec, "class", f"hierarchical.reconcilers[{i}]")
        params = spec.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"hierarchical.reconcilers[{i}].params: must be a mapping")
        out.append(ReconcilerSpec(name=name, class_path=class_path, params=dict(params)))
    return out


def _build_hierarchical_section(raw: dict) -> HierarchicalSectionConfig:
    reconcilers = _build_reconcilers(require(raw, "reconcilers", "hierarchical"))
    diagnostics = bool(raw.get("diagnostics", True))
    return HierarchicalSectionConfig(reconcilers=reconcilers, diagnostics=diagnostics)


def _build_hierarchical_evaluation(raw: dict) -> HierarchicalEvaluationConfig:
    metrics = require(raw, "metrics", "evaluation")
    if not isinstance(metrics, list) or not metrics:
        raise ConfigError("evaluation.metrics: must be a non-empty list")
    bad = [m for m in metrics if m not in HIERARCHICAL_METRICS]
    if bad:
        raise ConfigError(
            f"evaluation.metrics: unsupported {bad} (MVP hierarchical: {sorted(HIERARCHICAL_METRICS)})"
        )
    return HierarchicalEvaluationConfig(metrics=list(metrics))


def _build_hierarchical_config(raw: dict) -> HierarchicalConfig:
    """把层级 YAML 根 mapping 转成 HierarchicalConfig。"""
    data = _build_hierarchical_data(require(raw, "data", "config"))
    base_forecast = _build_base_forecast(require(raw, "base_forecast", "config"))
    hierarchical = _build_hierarchical_section(require(raw, "hierarchical", "config"))
    evaluation = _build_hierarchical_evaluation(require(raw, "evaluation", "config"))
    runtime = build_runtime(raw.get("runtime") or {})
    artifacts = build_artifacts(require(raw, "artifacts", "config"))
    seed = raw.get("seed", 0)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ConfigError("seed must be an integer")
    return HierarchicalConfig(
        data=data,
        base_forecast=base_forecast,
        hierarchical=hierarchical,
        evaluation=evaluation,
        runtime=runtime,
        artifacts=artifacts,
        seed=seed,
    )


def validate_hierarchical(config: HierarchicalConfig) -> HierarchicalConfig:
    """执行层级配置跨字段校验；基础类型和必填项已在 build 阶段完成。"""
    level = config.runtime.log_level.upper()
    if level not in VALID_LOG_LEVELS:
        raise ConfigError(
            f"runtime.log_level '{config.runtime.log_level}' invalid "
            f"({sorted(VALID_LOG_LEVELS)})"
        )
    config.runtime.log_level = level
    if not config.artifacts.output_dir.strip():
        raise ConfigError("artifacts.output_dir must be a non-empty string")
    return config


def load_hierarchical_config(path: str | Path) -> HierarchicalConfig:
    """读取层级 YAML，并返回已经校验过的 HierarchicalConfig。"""
    p, raw = load_yaml_mapping(path)
    config = _build_hierarchical_config(raw)
    config.config_source = str(p.resolve())
    validate_hierarchical(config)
    return config


def resolve_hierarchical_overrides(
    config: HierarchicalConfig,
    *,
    run_id: str | None = None,
    output_dir: str | None = None,
    log_name: str | None = None,
    log_level: str | None = None,
) -> HierarchicalConfig:
    """应用 CLI 运行级覆盖；覆盖后再次校验，保证 dry-run 也能提前失败。"""
    return apply_run_overrides(
        config,
        run_id=run_id,
        output_dir=output_dir,
        log_name=log_name,
        log_level=log_level,
        validate=validate_hierarchical,
    )
