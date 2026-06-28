"""Nixtla 后端适配器。

stats adapter 对应基础依赖,顶部直接暴露;ml/neural adapter 通过模块级
``__getattr__`` 延迟加载,保证未安装 ``ml``/``neural`` extra 的基础安装
仍能 import 主包(与各 adapter 模块 docstring 声明的 lazy 契约一致)。
"""

from tsforecasting.models.nixtla.stats import StatsForecastAdapter


def __getattr__(name):
    if name == "MLForecastAdapter":
        from tsforecasting.models.nixtla.ml import MLForecastAdapter

        return MLForecastAdapter
    if name == "NeuralForecastAdapter":
        from tsforecasting.models.nixtla.neural import NeuralForecastAdapter

        return NeuralForecastAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["StatsForecastAdapter", "MLForecastAdapter", "NeuralForecastAdapter"]
