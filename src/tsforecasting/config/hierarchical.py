"""Hierarchical reconciliation config (P9).

Independent from the MVP-0 ``Config``: a ``datasetsforecast`` data source, a
``base_forecast`` section (MVP: statsforecast presets) plus a ``hierarchical``
section of reconciler specs, and its own artifact set
(``base_predictions`` / ``reconciled_predictions`` / ``reconciliation_diagnostics``).
Stdlib-only validation, mirroring ``config/schema.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tsforecasting.config.schema import (
    VALID_LOG_LEVELS,
    ArtifactsConfig,
    ConfigError,
    ModelConfig,
    RuntimeConfig,
    _build_artifacts,
    _build_runtime,
    _require,
    _require_pos_int,
    _require_str,
    generate_run_id,
)

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
    # resolved at run time:
    run_id: str | None = None
    config_source: str | None = None


def _build_hierarchical_data(raw: dict) -> HierarchicalDataConfig:
    source = _require_str(raw, "source", "data")
    if source not in VALID_HIERARCHICAL_SOURCES:
        raise ConfigError(
            f"data.source '{source}' not supported (MVP: {sorted(VALID_HIERARCHICAL_SOURCES)})"
        )
    dataset = _require_str(raw, "dataset", "data")
    freq = _require_str(raw, "freq", "data")
    cache_dir = raw.get("cache_dir", "dataset/datasetsforecast_cache")
    if not isinstance(cache_dir, str) or not cache_dir.strip():
        raise ConfigError("data.cache_dir must be a non-empty string")
    return HierarchicalDataConfig(
        source=source, dataset=dataset, freq=freq, cache_dir=cache_dir
    )


def _build_base_models(raw: Any, backend: str) -> list[ModelConfig]:
    if not isinstance(raw, list) or not raw:
        raise ConfigError("base_forecast.models: must be a non-empty list")
    out: list[ModelConfig] = []
    names: set[str] = set()
    for i, m in enumerate(raw):
        if not isinstance(m, dict):
            raise ConfigError(f"base_forecast.models[{i}]: must be a mapping")
        name = _require_str(m, "name", f"base_forecast.models[{i}]")
        if name in names:
            raise ConfigError(f"base_forecast.models[{i}]: duplicate name '{name}'")
        names.add(name)
        params = m.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"base_forecast.models[{i}].params: must be a mapping")
        # backend comes from base_forecast.backend, not per-model.
        out.append(ModelConfig(name=name, backend=backend, params=dict(params)))
    return out


def _build_base_forecast(raw: dict) -> BaseForecastConfig:
    backend = _require_str(raw, "backend", "base_forecast")
    if backend not in HIERARCHICAL_BASE_BACKENDS:
        raise ConfigError(
            f"base_forecast.backend '{backend}' not supported "
            f"(MVP: {sorted(HIERARCHICAL_BASE_BACKENDS)})"
        )
    models = _build_base_models(_require(raw, "models", "base_forecast"), backend)
    horizon = _require_pos_int(raw, "horizon", "base_forecast")
    return BaseForecastConfig(backend=backend, models=models, horizon=horizon)


def _build_reconcilers(raw: Any) -> list[ReconcilerSpec]:
    if not isinstance(raw, list) or not raw:
        raise ConfigError("hierarchical.reconcilers: must be a non-empty list")
    out: list[ReconcilerSpec] = []
    names: set[str] = set()
    for i, spec in enumerate(raw):
        if not isinstance(spec, dict):
            raise ConfigError(f"hierarchical.reconcilers[{i}]: must be a mapping")
        name = _require_str(spec, "name", f"hierarchical.reconcilers[{i}]")
        if name in names:
            raise ConfigError(f"hierarchical.reconcilers[{i}]: duplicate name '{name}'")
        names.add(name)
        class_path = _require_str(spec, "class", f"hierarchical.reconcilers[{i}]")
        params = spec.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ConfigError(f"hierarchical.reconcilers[{i}].params: must be a mapping")
        out.append(ReconcilerSpec(name=name, class_path=class_path, params=dict(params)))
    return out


def _build_hierarchical_section(raw: dict) -> HierarchicalSectionConfig:
    reconcilers = _build_reconcilers(_require(raw, "reconcilers", "hierarchical"))
    diagnostics = bool(raw.get("diagnostics", True))
    return HierarchicalSectionConfig(reconcilers=reconcilers, diagnostics=diagnostics)


def _build_hierarchical_evaluation(raw: dict) -> HierarchicalEvaluationConfig:
    metrics = _require(raw, "metrics", "evaluation")
    if not isinstance(metrics, list) or not metrics:
        raise ConfigError("evaluation.metrics: must be a non-empty list")
    bad = [m for m in metrics if m not in HIERARCHICAL_METRICS]
    if bad:
        raise ConfigError(
            f"evaluation.metrics: unsupported {bad} (MVP hierarchical: {sorted(HIERARCHICAL_METRICS)})"
        )
    return HierarchicalEvaluationConfig(metrics=list(metrics))


def _build_hierarchical_config(raw: dict) -> HierarchicalConfig:
    data = _build_hierarchical_data(_require(raw, "data", "config"))
    base_forecast = _build_base_forecast(_require(raw, "base_forecast", "config"))
    hierarchical = _build_hierarchical_section(_require(raw, "hierarchical", "config"))
    evaluation = _build_hierarchical_evaluation(_require(raw, "evaluation", "config"))
    runtime = _build_runtime(raw.get("runtime") or {})
    artifacts = _build_artifacts(_require(raw, "artifacts", "config"))
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
    """Cross-field validation. Type/required-key checks happen at build time."""
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
    """Load and validate a hierarchical YAML config file."""
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {path}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")
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
    return validate_hierarchical(config)
