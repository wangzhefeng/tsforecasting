"""MLForecast backend adapter.

Wraps the native MLForecast ``fit`` / ``predict`` / ``cross_validation`` APIs
and normalizes their wide output into the unified long-table artifact contracts
(predictions.csv / backtest_predictions.csv), including the framework-derived
``horizon`` column. Mirrors ``StatsForecastAdapter`` surface-for-surface so the
orchestration layer can treat both backends uniformly.

Timing: like StatsForecast, the adapter fits all configured models in one
batched MLForecast object, so ``fit`` / ``predict`` / ``cross_validation``
timings are batch-level and shared across models in ``runtime_metrics``.

``mlforecast`` is imported at module top, but this module is only imported by
the orchestration layer inside the ``mlforecast`` backend branch, so the base
package (without the ``ml`` extra) still imports cleanly.
"""

from __future__ import annotations

import importlib
import time
from typing import Any

import pandas as pd
from mlforecast import MLForecast

from tsforecasting.artifacts.schema import (
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.config import MLForecastConfig
from tsforecasting.models.nixtla.stats import NON_MODEL_COLS_CV, NON_MODEL_COLS_FORECAST
from tsforecasting.models.registry import BuiltModel


def _resolve_target_transforms(specs: list[dict[str, Any]]) -> list[Any]:
    """Instantiate target transforms from a serializable ``{class, args?, kwargs?}`` spec."""
    transforms: list[Any] = []
    for spec in specs:
        module_path, _, cls_name = spec["class"].rpartition(".")
        if not module_path or not cls_name:
            raise ValueError(f"invalid target_transform class path '{spec['class']}'")
        cls = getattr(importlib.import_module(module_path), cls_name)
        transforms.append(cls(*spec.get("args") or [], **(spec.get("kwargs") or {})))
    return transforms


class MLForecastAdapter:
    """Adapt MLForecast batched output to the unified long contracts."""

    backend = "mlforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
        mlforecast_config: MLForecastConfig,
        n_jobs: int = 1,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
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
        # MLForecast emits one column per model in ``models=`` list order.
        if len(model_cols) != len(self._built):
            raise ValueError(
                f"model column count {len(model_cols)} != built models {len(self._built)}"
            )
        return {col: self._built[i].name for i, col in enumerate(model_cols)}

    def predict(self, h: int) -> pd.DataFrame:
        t0 = time.perf_counter()
        self._mlf.fit(self._df)
        self.timing["fit_seconds"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        fcst = self._mlf.predict(h)
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
        # horizon = step index of ds within each (unique_id, cutoff) window;
        # equals (ds - cutoff) / freq for a regular grid, but rank is robust.
        long["horizon"] = (
            long.groupby(["unique_id", "cutoff"])["ds"].rank(method="dense").astype(int)
        )
        return long[list(BACKTEST_PREDICTIONS_COLUMNS)]

    @property
    def model_types(self) -> dict[str, str]:
        return {m.name: m.model_type for m in self._built}
