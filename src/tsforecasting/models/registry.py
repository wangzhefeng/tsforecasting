"""模型 preset registry。

把 YAML 中的 ``models[].name`` 映射到真实类路径和元数据（backend、model_type、
dependency_group 等）。配置校验只读取这些元数据；真正的动态 import 和实例化
发生在 workflow 构建模型阶段。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from tsforecasting.utils.imports import instantiate_from_spec, resolve_class

if TYPE_CHECKING:
    from tsforecasting.config import Config, ModelConfig


class RegistryError(ValueError):
    """模型未知或配置 backend 与 registry 元数据不匹配时抛出。"""


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
    # MLForecast 的 class_path 指向内部 sklearn regressor；adapter 会把这些
    # regressor 统一包进一个 MLForecast 框架对象。
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
    # NeuralForecast 的 class_path 指向具体神经网络模型类；训练步数、输入窗口等
    # 超参来自 models[].params，adapter 再统一包进 NeuralForecast。
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
    # 区间预测 preset：通过可序列化 loss spec 构造 MQLoss，让模型输出 median
    # 点预测和 lo-/hi- 区间列，同时保持 run_config.yaml 可读可复现。
    RegistryEntry(
        backend="neuralforecast",
        model_name="nhits_quantile",
        class_path="neuralforecast.models.NHITS",
        model_type="neural_quantile",
        mvp_preset=True,
        status="mvp_smoke",
        dependency_group="neural",
    ),
]


def get_entry(model_name: str) -> RegistryEntry:
    """按 ``model_name`` 查 REGISTRY 条目;未知名称抛 RegistryError 并列出已知模型。"""
    index = {entry.model_name: entry for entry in REGISTRY}
    if model_name not in index:
        raise RegistryError(f"model '{model_name}' not in registry; known: {sorted(index)}")

    return index[model_name]


def build_model(model: "ModelConfig") -> BuiltModel:
    """校验 backend 一致后动态 import 模型类,把可序列化 loss spec 转成实例再实例化。"""
    entry = get_entry(model.name)
    if entry.backend != model.backend:
        raise RegistryError(
            f"model '{model.name}': config backend '{model.backend}' "
            f"!= registry backend '{entry.backend}'"
        )
    cls = resolve_class(entry.class_path)
    params = dict(model.params)
    # 将 YAML 中可序列化的 loss spec 转成真实 loss 实例，避免配置文件写入对象。
    if isinstance(params.get("loss"), dict):
        spec = params.pop("loss")
        if not isinstance(spec.get("class"), str) or not spec["class"].strip():
            raise RegistryError(f"model '{model.name}': loss.class must be a string")
        kwargs = spec.get("kwargs") or {}
        if not isinstance(kwargs, dict):
            raise RegistryError(f"model '{model.name}': loss.kwargs must be a mapping")
        params["loss"] = instantiate_from_spec(spec["class"], kwargs)
    return BuiltModel(
        name=model.name,
        backend=entry.backend,
        model_type=entry.model_type,
        instance=cls(**params),
    )


def build_models(config: "Config") -> list[BuiltModel]:
    """按 config.models 顺序实例化模型，保留后续输出列到模型名的映射顺序。"""
    return [build_model(m) for m in config.models]
