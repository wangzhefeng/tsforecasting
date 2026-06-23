"""NeuralForecast backend adapter.

Wraps the native NeuralForecast ``fit`` / ``predict`` / ``cross_validation``
APIs and normalizes their wide output into the unified long-table artifact
contracts (predictions.csv / backtest_predictions.csv), including the
framework-derived ``horizon`` column. Mirrors ``StatsForecastAdapter`` /
``MLForecastAdapter`` surface-for-surface so the orchestration layer can treat
all backends uniformly.

Unlike MLForecast, NeuralForecast carries its training hyperparams (``h``,
``input_size``, ``max_steps``, ...) on each model instance, so they flow through
``models[].params`` and this adapter needs no extra shared config. The adapter
does pass ``val_size=h`` to fit / cross-validation to begin handling
NeuralForecast's validation semantics without touching the MVP-0 backtest
contract.

Timing: like the other backends, all configured models are fit in one batched
NeuralForecast object, so the timings are batch-level and shared across models
in ``runtime_metrics``.

``neuralforecast`` is imported at module top, but this module is only imported
by the orchestration layer inside the ``neuralforecast`` backend branch, so the
base package (without the ``neural`` extra) still imports cleanly.
"""

from __future__ import annotations

import time

import pandas as pd
from neuralforecast import NeuralForecast

from tsforecasting.artifacts.schema import (
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.models.nixtla.stats import NON_MODEL_COLS_CV, NON_MODEL_COLS_FORECAST
from tsforecasting.models.registry import BuiltModel


class NeuralForecastAdapter:
    """Adapt NeuralForecast batched output to the unified long contracts."""

    backend = "neuralforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
        self._nf = NeuralForecast(models=[m.instance for m in built_models], freq=freq)
        self.timing: dict[str, float] = {
            "fit_seconds": 0.0,
            "predict_seconds": 0.0,
            "cross_validation_seconds": 0.0,
        }

    def _name_map(self, model_cols: list[str]) -> dict[str, str]:
        # NeuralForecast emits one column per model (named after each model's
        # alias) in ``models=`` list order.
        if len(model_cols) != len(self._built):
            raise ValueError(
                f"model column count {len(model_cols)} != built models {len(self._built)}"
            )
        return {col: self._built[i].name for i, col in enumerate(model_cols)}

    def predict(self, h: int) -> pd.DataFrame:
        t0 = time.perf_counter()
        self._nf.fit(self._df, val_size=h)
        self.timing["fit_seconds"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        fcst = self._nf.predict(h=h)
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
        cv = self._nf.cross_validation(
            df=self._df,
            h=h,
            n_windows=n_windows,
            step_size=step_size,
            val_size=h,
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
