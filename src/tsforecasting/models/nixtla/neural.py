"""NeuralForecast backend adapter.

Wraps the native NeuralForecast ``fit`` / ``predict`` / ``cross_validation``
APIs and normalizes their wide output into the unified long-table artifact
contracts (predictions.csv / backtest_predictions.csv), including the
framework-derived ``horizon`` column. Mirrors ``StatsForecastAdapter`` /
``MLForecastAdapter`` surface-for-surface so the orchestration layer can treat
all backends uniformly.

When ``levels`` is provided the ``lo-{level}``/``hi-{level}`` columns are
appended. NeuralForecast emits these from a quantile-loss model (e.g.
``NHITS(loss=MQLoss)``) with column names like ``NHITS-lo-80.0`` /
``NHITS-median``; this adapter strips the trailing ``.0`` and uses ``median``
as the point forecast, then reuses the shared ``melt_forecast_long`` helper.

Timing: all configured models are fit in one batched NeuralForecast object, so
the timings are batch-level and shared across models in ``runtime_metrics``.

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
from tsforecasting.models.nixtla.stats import (
    NON_MODEL_COLS_CV,
    NON_MODEL_COLS_FORECAST,
    _is_pure_model_col,
    interval_columns,
    melt_forecast_long,
)
from tsforecasting.models.registry import BuiltModel


def _make_lightning_logger():
    """Route Lightning TensorBoard telemetry under ``logs/lightning/``.

    Without this, Lightning's default logger writes to ``./lightning_logs/``
    (one ``version_N/`` per fit). Routing under ``logs/`` keeps neural telemetry
    with the rest of the run logs. This NeuralForecast version takes
    ``trainer_kwargs`` on each *model* (not on ``NeuralForecast`` itself); the
    adapter merges this logger into every model's ``trainer_kwargs``, which the
    model then forwards to its Lightning ``Trainer``. The import is lazy so the
    base package (without the ``neural`` extra) still imports cleanly.
    """
    try:
        from lightning.pytorch.loggers import TensorBoardLogger
    except ImportError:  # older neuralforecast pins
        from pytorch_lightning.loggers import TensorBoardLogger
    return TensorBoardLogger(save_dir="logs", name="lightning")


def _normalize_neural_cols(wide: pd.DataFrame) -> pd.DataFrame:
    """Normalize NeuralForecast column names so the shared melt helper matches.

    - interval cols carry a trailing ``.0`` (``NHITS-lo-80.0`` -> ``NHITS-lo-80``)
    - the point forecast of a quantile model is ``NHITS-median`` -> ``NHITS``
      (interval cols are keyed on the model alias, not the median column)
    """
    rename: dict[str, str] = {}
    for c in wide.columns:
        if ("-lo-" in c or "-hi-" in c) and c.endswith(".0"):
            rename[c] = c[:-2]
        elif c.endswith("-median"):
            rename[c] = c[: -len("-median")]
    return wide.rename(columns=rename) if rename else wide


class NeuralForecastAdapter:
    """Adapt NeuralForecast batched output to the unified long contracts."""

    backend = "neuralforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
        levels: list[int] | None = None,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
        self._levels = list(levels) if levels else None
        # This NeuralForecast version builds its Lightning Trainer from each
        # model's trainer_kwargs; merge in a logger so TensorBoard telemetry
        # lands under logs/lightning/ instead of the default ./lightning_logs/.
        lightning_logger = _make_lightning_logger()
        for m in built_models:
            tk = dict(getattr(m.instance, "trainer_kwargs", {}) or {})
            tk["logger"] = lightning_logger
            m.instance.trainer_kwargs = tk
        self._nf = NeuralForecast(models=[m.instance for m in built_models], freq=freq)
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
        self._nf.fit(self._df, val_size=h)
        self.timing["fit_seconds"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        # quantile-loss models emit lo/hi from their quantiles; level not passed here
        fcst = self._nf.predict(h=h)
        self.timing["predict_seconds"] += time.perf_counter() - t0

        fcst = _normalize_neural_cols(fcst)
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
            cv = self._nf.cross_validation(
                df=self._df, h=h, n_windows=n_windows, step_size=step_size,
                val_size=h, level=self._levels,
            )
        else:
            cv = self._nf.cross_validation(
                df=self._df, h=h, n_windows=n_windows, step_size=step_size, val_size=h
            )
        self.timing["cross_validation_seconds"] += time.perf_counter() - t0

        cv = _normalize_neural_cols(cv)
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
