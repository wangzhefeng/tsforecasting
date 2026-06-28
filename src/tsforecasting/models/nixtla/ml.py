"""MLForecast 后端适配器。

负责调用 MLForecast 原生 ``fit`` / ``predict`` / ``cross_validation``，
并把 wide 输出归一到统一长表 artifact 契约（``predictions.csv`` /
``backtest_predictions.csv``）。类接口刻意与 ``StatsForecastAdapter`` 对齐，
让 workflow 可以按 backend 批量处理。

耗时语义：同一 backend 的所有模型被放进一个 MLForecast 对象中批量执行，
因此 ``runtime_metrics`` 中这些模型共享同一组 fit/predict/cv 耗时。

本模块只会在 workflow 的 ``mlforecast`` 分支里被导入，所以基础安装环境
未安装 ``ml`` extra 时仍能 import 主包。
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
from mlforecast import MLForecast

from tsforecasting.artifacts.schema import (
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.config import MLForecastConfig
from tsforecasting.models.registry import BuiltModel
from tsforecasting.utils.frames import (
    NON_MODEL_COLS_CV,
    NON_MODEL_COLS_FORECAST,
    add_dense_horizon,
    interval_columns,
    is_pure_model_col,
    melt_forecast_long,
)
from tsforecasting.utils.imports import instantiate_serialized_spec


def _resolve_target_transforms(specs: list[dict[str, Any]]) -> list[Any]:
    """把 YAML 中可序列化的 target_transform spec 实例化为真实对象。"""
    return [instantiate_serialized_spec(spec) for spec in specs]


class MLForecastAdapter:
    """把 MLForecast 批量输出适配成统一预测/回测长表。"""

    backend = "mlforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
        mlforecast_config: MLForecastConfig,
        n_jobs: int = 1,
        levels: list[int] | None = None,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
        self._levels = list(levels) if levels else None
        target_transforms = (
            _resolve_target_transforms(mlforecast_config.target_transforms)
            if mlforecast_config.target_transforms
            else None
        )
        self._mlf = MLForecast(
            models=[m.instance for m in built_models],
            freq=freq,
            lags=mlforecast_config.lags,
            date_features=mlforecast_config.date_features or None,
            target_transforms=target_transforms,
            num_threads=n_jobs,
        )
        self.timing: dict[str, float] = {
            "fit_seconds": 0.0,
            "predict_seconds": 0.0,
            "cross_validation_seconds": 0.0,
        }

    def _name_map(self, model_cols: list[str]) -> dict[str, str]:
        # MLForecast 按 models= 列表顺序输出每个模型的预测列。
        if len(model_cols) != len(self._built):
            raise ValueError(
                f"model column count {len(model_cols)} != built models {len(self._built)}"
            )
        return {col: self._built[i].name for i, col in enumerate(model_cols)}

    def predict(self, h: int) -> pd.DataFrame:
        t0 = time.perf_counter()
        if self._levels:
            from mlforecast.utils import PredictionIntervals

            self._mlf.fit(
                self._df, prediction_intervals=PredictionIntervals(h=h)
            )
        else:
            self._mlf.fit(self._df)
        self.timing["fit_seconds"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        if self._levels:
            fcst = self._mlf.predict(h, level=self._levels)
        else:
            fcst = self._mlf.predict(h)
        self.timing["predict_seconds"] += time.perf_counter() - t0

        pure = [
            c
            for c in fcst.columns
            if c not in NON_MODEL_COLS_FORECAST and is_pure_model_col(c)
        ]
        name_map = self._name_map(pure)
        long = melt_forecast_long(fcst, NON_MODEL_COLS_FORECAST, name_map, self._levels)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        return long[list(PREDICTIONS_COLUMNS) + interval_columns(self._levels)]

    def cross_validation(
        self, h: int, n_windows: int, step_size: int
    ) -> pd.DataFrame:
        t0 = time.perf_counter()
        cv = self._mlf.cross_validation(
            df=self._df, n_windows=n_windows, h=h, step_size=step_size
        )
        self.timing["cross_validation_seconds"] += time.perf_counter() - t0

        model_cols = [c for c in cv.columns if c not in NON_MODEL_COLS_CV]
        name_map = self._name_map(model_cols)
        long = cv.melt(
            id_vars=list(NON_MODEL_COLS_CV),
            value_vars=model_cols,
            var_name="_model_col",
            value_name="yhat",
        )
        long["model"] = long["_model_col"].map(name_map)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        long = long.sort_values(["unique_id", "cutoff", "model", "ds"]).reset_index(
            drop=True
        )
        # horizon 表示同一 (unique_id, cutoff) 窗口内 ds 的步数；rank 比直接
        # 用时间差除 freq 更能容忍 pandas/上游的频率表示差异。
        long = add_dense_horizon(long)
        return long[list(BACKTEST_PREDICTIONS_COLUMNS)]

    @property
    def model_types(self) -> dict[str, str]:
        return {m.name: m.model_type for m in self._built}
