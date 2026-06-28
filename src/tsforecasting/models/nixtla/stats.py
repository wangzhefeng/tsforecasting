"""StatsForecast 后端适配器。

负责调用 StatsForecast 原生 ``fit`` / ``predict`` / ``cross_validation``，
再把 wide 输出归一到统一长表 artifact 契约。配置预测区间时使用上游
``level=`` 参数，并以增量列形式追加 ``lo-{level}`` / ``hi-{level}``。
"""

from __future__ import annotations

import time

import pandas as pd
from statsforecast import StatsForecast

from tsforecasting.artifacts.schema import (
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.models.registry import BuiltModel
from tsforecasting.utils.frames import (
    NON_MODEL_COLS_CV,
    NON_MODEL_COLS_FORECAST,
    add_dense_horizon,
    interval_columns,
    is_pure_model_col,
    melt_forecast_long,
)


class StatsForecastAdapter:
    """把 StatsForecast 批量输出适配成统一预测/回测长表。"""

    backend = "statsforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
        n_jobs: int = 1,
        levels: list[int] | None = None,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
        self._levels = list(levels) if levels else None
        self._sf = StatsForecast(
            models=[m.instance for m in built_models], freq=freq, n_jobs=n_jobs
        )
        self.timing: dict[str, float] = {
            "fit_seconds": 0.0,
            "predict_seconds": 0.0,
            "cross_validation_seconds": 0.0,
        }

    def _name_map(self, model_cols: list[str]) -> dict[str, str]:
        """按上游输出列顺序映射回配置里的模型名。"""
        if len(model_cols) != len(self._built):
            raise ValueError(
                f"model column count {len(model_cols)} != built models {len(self._built)}"
            )
        return {col: self._built[i].name for i, col in enumerate(model_cols)}

    def predict(self, h: int) -> pd.DataFrame:
        t0 = time.perf_counter()
        self._sf.fit(self._df)
        self.timing["fit_seconds"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        if self._levels:
            fcst = self._sf.predict(h=h, level=self._levels)
        else:
            fcst = self._sf.predict(h=h)
        self.timing["predict_seconds"] += time.perf_counter() - t0

        pure = [
            c
            for c in fcst.columns
            if c not in NON_MODEL_COLS_FORECAST and is_pure_model_col(c)
        ]
        long = melt_forecast_long(fcst, NON_MODEL_COLS_FORECAST, self._name_map(pure), self._levels)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        return long[list(PREDICTIONS_COLUMNS) + interval_columns(self._levels)]

    def cross_validation(
        self, h: int, n_windows: int, step_size: int
    ) -> pd.DataFrame:
        t0 = time.perf_counter()
        if self._levels:
            cv = self._sf.cross_validation(
                df=self._df, h=h, n_windows=n_windows, step_size=step_size,
                level=self._levels,
            )
        else:
            cv = self._sf.cross_validation(
                df=self._df, h=h, n_windows=n_windows, step_size=step_size
            )
        self.timing["cross_validation_seconds"] += time.perf_counter() - t0

        pure = [
            c
            for c in cv.columns
            if c not in NON_MODEL_COLS_CV and is_pure_model_col(c)
        ]
        long = melt_forecast_long(cv, NON_MODEL_COLS_CV, self._name_map(pure), self._levels)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        long = long.sort_values(["unique_id", "cutoff", "model", "ds"]).reset_index(
            drop=True
        )
        long = add_dense_horizon(long)
        return long[list(BACKTEST_PREDICTIONS_COLUMNS) + interval_columns(self._levels)]

    @property
    def model_types(self) -> dict[str, str]:
        return {m.name: m.model_type for m in self._built}
