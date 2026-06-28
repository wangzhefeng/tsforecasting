"""Nixtla 后端适配器。"""

from tsforecasting.models.nixtla.ml import MLForecastAdapter
from tsforecasting.models.nixtla.neural import NeuralForecastAdapter
from tsforecasting.models.nixtla.stats import StatsForecastAdapter

__all__ = [
    "StatsForecastAdapter",
    "MLForecastAdapter",
    "NeuralForecastAdapter",
]
