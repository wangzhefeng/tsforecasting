"""Preset registry.

Maps config model names to their ``class_path`` plus metadata (backend,
model_type, status, dependency_group). MVP-0 registers the two StatsForecast
smoke models; MVP-1 adds the MLForecast sklearn presets. The full Nixtla
catalog is a Phase-2 concern.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from tsforecasting.config import Config, ModelConfig


class RegistryError(ValueError):
    """Raised when a model is unknown or its backend mismatches the registry."""


@dataclass(frozen=True)
class RegistryEntry:
    backend: str
    model_name: str
    class_path: str
    model_type: str
    mvp_preset: bool
    status: str
    dependency_group: str


@dataclass
class BuiltModel:
    name: str
    backend: str
    model_type: str
    instance: Any


REGISTRY: list[RegistryEntry] = [
    RegistryEntry(
        backend="statsforecast",
        model_name="seasonal_naive",
        class_path="statsforecast.models.SeasonalNaive",
        model_type="naive",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="core",
    ),
    RegistryEntry(
        backend="statsforecast",
        model_name="auto_ets",
        class_path="statsforecast.models.AutoETS",
        model_type="ets",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="core",
    ),
    # MLForecast sklearn presets (MVP-1). class_path targets the inner sklearn
    # regressor; build_model instantiates it via cls(**params) and the
    # MLForecastAdapter wraps the instances in one MLForecast framework object.
    RegistryEntry(
        backend="mlforecast",
        model_name="linear_regression",
        class_path="sklearn.linear_model.LinearRegression",
        model_type="linear",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="ml",
    ),
    RegistryEntry(
        backend="mlforecast",
        model_name="ridge",
        class_path="sklearn.linear_model.Ridge",
        model_type="ridge",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="ml",
    ),
    RegistryEntry(
        backend="mlforecast",
        model_name="lasso",
        class_path="sklearn.linear_model.Lasso",
        model_type="lasso",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="ml",
    ),
    RegistryEntry(
        backend="mlforecast",
        model_name="elastic_net",
        class_path="sklearn.linear_model.ElasticNet",
        model_type="elasticnet",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="ml",
    ),
    RegistryEntry(
        backend="mlforecast",
        model_name="random_forest",
        class_path="sklearn.ensemble.RandomForestRegressor",
        model_type="random_forest",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="ml",
    ),
    RegistryEntry(
        backend="mlforecast",
        model_name="hist_gradient_boosting",
        class_path="sklearn.ensemble.HistGradientBoostingRegressor",
        model_type="hist_gbm",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="ml",
    ),
    # NeuralForecast CPU-smoke presets (MVP-1). class_path targets the neural
    # model class; build_model instantiates it via cls(**params) (params carry
    # h / input_size / max_steps) and the NeuralForecastAdapter wraps the
    # instances in one NeuralForecast framework object.
    RegistryEntry(
        backend="neuralforecast",
        model_name="nhits",
        class_path="neuralforecast.models.NHITS",
        model_type="neural",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="neural",
    ),
    RegistryEntry(
        backend="neuralforecast",
        model_name="nbeats",
        class_path="neuralforecast.models.NBEATS",
        model_type="neural",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="neural",
    ),
]


def _index() -> dict[str, RegistryEntry]:
    return {entry.model_name: entry for entry in REGISTRY}


def get_entry(model_name: str) -> RegistryEntry:
    index = _index()
    if model_name not in index:
        raise RegistryError(
            f"model '{model_name}' not in registry; known: {sorted(index)}"
        )
    return index[model_name]


def _import_class(class_path: str) -> type:
    module_path, _, cls_name = class_path.rpartition(".")
    if not module_path or not cls_name:
        raise RegistryError(f"invalid class_path '{class_path}'")
    module = importlib.import_module(module_path)
    return getattr(module, cls_name)


def build_model(model: ModelConfig) -> BuiltModel:
    entry = get_entry(model.name)
    if entry.backend != model.backend:
        raise RegistryError(
            f"model '{model.name}': config backend '{model.backend}' "
            f"!= registry backend '{entry.backend}'"
        )
    cls = _import_class(entry.class_path)
    return BuiltModel(
        name=model.name,
        backend=entry.backend,
        model_type=entry.model_type,
        instance=cls(**model.params),
    )


def build_models(config: Config) -> list[BuiltModel]:
    """Instantiate one BuiltModel per entry in ``config.models``."""
    return [build_model(m) for m in config.models]
