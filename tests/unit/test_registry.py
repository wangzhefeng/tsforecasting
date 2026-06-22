"""Tests for the MVP-0 preset registry."""

from __future__ import annotations

import pytest

from tsforecasting.config import (
    ArtifactsConfig,
    BacktestConfig,
    Config,
    DataConfig,
    EvaluationConfig,
    ModelConfig,
    RuntimeConfig,
)
from tsforecasting.models import (
    REGISTRY,
    BuiltModel,
    RegistryError,
    build_model,
    build_models,
    get_entry,
)


def _config(models: list[ModelConfig]) -> Config:
    return Config(
        data=DataConfig(path="x", time_col="date", target_col="OT", freq="1h"),
        backtest=BacktestConfig(horizon=24, n_windows=3, step_size=24),
        models=models,
        evaluation=EvaluationConfig(metrics=["mae"]),
        runtime=RuntimeConfig(),
        artifacts=ArtifactsConfig(output_dir="runs/x"),
    )


def test_registry_contains_mvp0_models() -> None:
    names = {e.model_name for e in REGISTRY}
    assert {"seasonal_naive", "auto_ets"} <= names
    assert all(e.dependency_group == "core" for e in REGISTRY)
    assert all(e.backend == "statsforecast" for e in REGISTRY)


def test_get_entry_known_and_unknown() -> None:
    assert get_entry("seasonal_naive").class_path == "statsforecast.models.SeasonalNaive"
    with pytest.raises(RegistryError, match="not in registry"):
        get_entry("nope")


def test_build_model_instantiates_with_params() -> None:
    built = build_model(
        ModelConfig(name="seasonal_naive", backend="statsforecast", params={"season_length": 24})
    )
    assert isinstance(built, BuiltModel)
    assert built.model_type == "naive"
    assert built.backend == "statsforecast"
    from statsforecast.models import SeasonalNaive

    assert isinstance(built.instance, SeasonalNaive)


def test_build_models_from_config() -> None:
    config = _config(
        [
            ModelConfig(name="seasonal_naive", backend="statsforecast", params={"season_length": 24}),
            ModelConfig(name="auto_ets", backend="statsforecast", params={"season_length": 24}),
        ]
    )
    built = build_models(config)
    assert [b.name for b in built] == ["seasonal_naive", "auto_ets"]
    from statsforecast.models import AutoETS, SeasonalNaive

    assert isinstance(built[0].instance, SeasonalNaive)
    assert isinstance(built[1].instance, AutoETS)


def test_backend_mismatch_raises() -> None:
    with pytest.raises(RegistryError, match="backend"):
        build_model(ModelConfig(name="seasonal_naive", backend="xgboost", params={}))
