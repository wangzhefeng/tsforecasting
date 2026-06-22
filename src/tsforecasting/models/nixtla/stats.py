"""StatsForecast backend adapter.

Wraps the native StatsForecast ``fit`` / ``predict`` / ``cross_validation``
APIs and normalizes their wide output into the unified long-table artifact
contracts (predictions.csv / backtest_predictions.csv), including the
framework-derived ``horizon`` column.

Timing: the adapter fits all configured models in one batched StatsForecast
object, so ``fit`` / ``predict`` / ``cross_validation`` timings are batch-level
and shared across models in ``runtime_metrics`` (acceptable for MVP-0; Phase 2
can move to per-model timing if needed).
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

NON_MODEL_COLS_FORECAST = ("unique_id", "ds")
NON_MODEL_COLS_CV = ("unique_id", "ds", "cutoff", "y")


class StatsForecastAdapter:
    """Adapt StatsForecast batched output to the unified long contracts."""

    backend = "statsforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
        n_jobs: int = 1,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
        self._sf = StatsForecast(
            models=[m.instance for m in built_models], freq=freq, n_jobs=n_jobs
        )
        self.timing: dict[str, float] = {
            "fit_seconds": 0.0,
            "predict_seconds": 0.0,
            "cross_validation_seconds": 0.0,
        }

    def _name_map(self, model_cols: list[str]) -> dict[str, str]:
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
        fcst = self._sf.predict(h=h)
        self.timing["predict_seconds"] += time.perf_counter() - t0

        model_cols = [c for c in fcst.columns if c not in NON_MODEL_COLS_FORECAST]
        name_map = self._name_map(model_cols)
        long = fcst.melt(
            id_vars=list(NON_MODEL_COLS_FORECAST),
            value_vars=model_cols,
            var_name="_model_col",
            value_name="yhat",
        )
        long["model"] = long["_model_col"].map(name_map)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        return long[list(PREDICTIONS_COLUMNS)]

    def cross_validation(
        self, h: int, n_windows: int, step_size: int
    ) -> pd.DataFrame:
        t0 = time.perf_counter()
        cv = self._sf.cross_validation(
            df=self._df, h=h, n_windows=n_windows, step_size=step_size
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
        # horizon = step index of ds within each (unique_id, cutoff) window;
        # equals (ds - cutoff) / freq for a regular grid, but rank is robust.
        long["horizon"] = (
            long.groupby(["unique_id", "cutoff"])["ds"].rank(method="dense").astype(int)
        )
        return long[list(BACKTEST_PREDICTIONS_COLUMNS)]

    @property
    def model_types(self) -> dict[str, str]:
        return {m.name: m.model_type for m in self._built}
