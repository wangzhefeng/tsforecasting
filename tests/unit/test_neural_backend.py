"""Tests for the NeuralForecast backend adapter output contracts.

Mirrors ``test_stats_backend.py`` / ``test_ml_backend.py``. Skipped entirely
when the ``neural`` extra (``neuralforecast``) is not installed, so the base
dependency set still passes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("neuralforecast")

from tsforecasting.artifacts import (  # noqa: E402
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.config import ModelConfig  # noqa: E402
from tsforecasting.models import build_model  # noqa: E402
from tsforecasting.models.nixtla.neural import NeuralForecastAdapter  # noqa: E402


def _df(n: int = 300) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="1h")
    y = np.sin(2 * np.pi * np.arange(n) / 24.0)  # period 24 -> matches input_size/seasonality
    return pd.DataFrame({"unique_id": "s0", "ds": idx, "y": y})


def _params() -> dict:
    # CPU smoke: tiny max_steps; enable_progress_bar keeps pytest output clean.
    return {"h": 24, "input_size": 24, "max_steps": 3, "enable_progress_bar": False}


def _built() -> list:
    return [
        build_model(ModelConfig(name="nhits", backend="neuralforecast", params=_params())),
        build_model(ModelConfig(name="nbeats", backend="neuralforecast", params=_params())),
    ]


def test_predict_produces_predictions_contract() -> None:
    adapter = NeuralForecastAdapter(df=_df(), built_models=_built(), freq="1h", run_id="r1")
    preds = adapter.predict(h=24)
    assert list(preds.columns) == PREDICTIONS_COLUMNS
    assert set(preds["model"]) == {"nhits", "nbeats"}
    assert (preds["backend"] == "neuralforecast").all()
    assert (preds["run_id"] == "r1").all()
    assert len(preds) == 24 * 2  # h steps x 2 models
    assert adapter.timing["fit_seconds"] >= 0.0
    assert adapter.timing["predict_seconds"] >= 0.0


def test_cross_validation_produces_backtest_contract_and_horizon() -> None:
    adapter = NeuralForecastAdapter(df=_df(), built_models=_built(), freq="1h", run_id="r1")
    bt = adapter.cross_validation(h=24, n_windows=3, step_size=24)
    assert list(bt.columns) == BACKTEST_PREDICTIONS_COLUMNS
    assert set(bt["horizon"]) == set(range(1, 25))
    # each (unique_id, cutoff) window carries h steps x n_models rows
    counts = bt.groupby(["unique_id", "cutoff"]).size()
    assert (counts == 24 * 2).all()
    assert adapter.timing["cross_validation_seconds"] >= 0.0


def test_model_types_exposed() -> None:
    adapter = NeuralForecastAdapter(df=_df(), built_models=_built(), freq="1h", run_id="r1")
    assert adapter.model_types == {"nhits": "neural", "nbeats": "neural"}
