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
        artifacts=ArtifactsConfig(output_dir="results/x"),
    )


def test_registry_contains_mvp0_models() -> None:
    names = {e.model_name for e in REGISTRY}
    assert {"seasonal_naive", "auto_ets"} <= names
    # statsforecast entries stay on the core dependency group
    stats_entries = [e for e in REGISTRY if e.backend == "statsforecast"]
    assert all(e.dependency_group == "core" for e in stats_entries)


def test_registry_contains_mlforecast_presets() -> None:
    ml_entries = [e for e in REGISTRY if e.backend == "mlforecast"]
    names = {e.model_name for e in ml_entries}
    assert {
        "linear_regression",
        "ridge",
        "lasso",
        "elastic_net",
        "random_forest",
        "hist_gradient_boosting",
    } <= names
    assert all(e.dependency_group == "ml" for e in ml_entries)
    assert all(e.class_path.startswith("sklearn.") for e in ml_entries)


def test_registry_contains_neuralforecast_presets() -> None:
    neural_entries = [e for e in REGISTRY if e.backend == "neuralforecast"]
    names = {e.model_name for e in neural_entries}
    assert {"nhits", "nbeats"} <= names
    assert all(e.dependency_group == "neural" for e in neural_entries)
    assert all(e.class_path.startswith("neuralforecast.models.") for e in neural_entries)


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


def test_build_model_instantiates_mlforecast_preset() -> None:
    pytest.importorskip("sklearn")
    built = build_model(
        ModelConfig(name="random_forest", backend="mlforecast", params={"n_estimators": 5})
    )
    assert built.backend == "mlforecast"
    assert built.model_type == "random_forest"
    from sklearn.ensemble import RandomForestRegressor

    assert isinstance(built.instance, RandomForestRegressor)


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


def test_build_model_resolves_loss_spec() -> None:
    pytest.importorskip("neuralforecast")
    built = build_model(
        ModelConfig(
            name="nhits_quantile",
            backend="neuralforecast",
            params={
                "h": 4,
                "input_size": 8,
                "max_steps": 1,
                "loss": {
                    "class": "neuralforecast.losses.pytorch.MQLoss",
                    "kwargs": {"quantiles": [0.1, 0.5, 0.9]},
                },
            },
        )
    )
    from neuralforecast.losses.pytorch import MQLoss

    assert isinstance(built.instance.loss, MQLoss)
    assert built.model_type == "neural_quantile"
