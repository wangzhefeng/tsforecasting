"""StatsForecast backend adapter + shared wide->long interval melt helper.

The ``melt_forecast_long`` helper is shared by the ml/neural adapters so the
optional ``lo-{level}``/``hi-{level}`` columns are appended consistently.

When ``levels`` is provided the native ``level=`` argument is used and the
interval columns are appended (contract-additive: required columns unchanged).
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


def _is_pure_model_col(col: str) -> bool:
    return "-lo-" not in col and "-hi-" not in col


def interval_columns(levels: list[int] | None) -> list[str]:
    out: list[str] = []
    if levels:
        for level in levels:
            out += [f"lo-{level}", f"hi-{level}"]
    return out


def melt_forecast_long(
    wide: pd.DataFrame,
    non_model_cols: tuple[str, ...],
    name_map: dict[str, str],
    levels: list[int] | None,
) -> pd.DataFrame:
    """Melt a wide forecast/cv frame to the unified long contract.

    Without ``levels`` this is a plain melt of the model columns. With
    ``levels`` it emits one block per model, renaming that model's
    ``{col}-lo-{l}``/``{col}-hi-{l}`` columns to ``lo-{l}``/``hi-{l}``.
    """
    model_cols = [
        c for c in wide.columns if c not in non_model_cols and _is_pure_model_col(c)
    ]
    if not levels:
        long = wide.melt(
            id_vars=list(non_model_cols),
            value_vars=model_cols,
            var_name="_model_col",
            value_name="yhat",
        )
        long["model"] = long["_model_col"].map(name_map)
        return long
    parts: list[pd.DataFrame] = []
    for mc in model_cols:
        cols = list(non_model_cols) + [mc]
        rename: dict[str, str] = {mc: "yhat"}
        for level in levels:
            lo, hi = f"{mc}-lo-{level}", f"{mc}-hi-{level}"
            cols += [lo, hi]
            rename[lo] = f"lo-{level}"
            rename[hi] = f"hi-{level}"
        sub = wide[cols].rename(columns=rename)
        sub["model"] = name_map[mc]
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


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

        pure = [c for c in fcst.columns if c not in NON_MODEL_COLS_FORECAST and _is_pure_model_col(c)]
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

        pure = [c for c in cv.columns if c not in NON_MODEL_COLS_CV and _is_pure_model_col(c)]
        long = melt_forecast_long(cv, NON_MODEL_COLS_CV, self._name_map(pure), self._levels)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        long = long.sort_values(["unique_id", "cutoff", "model", "ds"]).reset_index(
            drop=True
        )
        long["horizon"] = (
            long.groupby(["unique_id", "cutoff"])["ds"].rank(method="dense").astype(int)
        )
        return long[list(BACKTEST_PREDICTIONS_COLUMNS) + interval_columns(self._levels)]

    @property
    def model_types(self) -> dict[str, str]:
        return {m.name: m.model_type for m in self._built}
