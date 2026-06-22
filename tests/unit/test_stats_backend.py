"""Tests for the StatsForecast backend adapter output contracts."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tsforecasting.artifacts import (
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.config import ModelConfig
from tsforecasting.models import build_model
from tsforecasting.models.nixtla import StatsForecastAdapter


def _df(n: int = 200) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="1h")
    y = np.sin(2 * np.pi * np.arange(n) / 24.0)  # period 24 -> matches season_length
    return pd.DataFrame({"unique_id": "s0", "ds": idx, "y": y})


def _built() -> list:
    return [
        build_model(
            ModelConfig(name="seasonal_naive", backend="statsforecast", params={"season_length": 24})
        ),
        build_model(
            ModelConfig(name="auto_ets", backend="statsforecast", params={"season_length": 24})
        ),
    ]


def test_predict_produces_predictions_contract() -> None:
    adapter = StatsForecastAdapter(df=_df(), built_models=_built(), freq="1h", run_id="r1")
    preds = adapter.predict(h=24)
    assert list(preds.columns) == PREDICTIONS_COLUMNS
    assert set(preds["model"]) == {"seasonal_naive", "auto_ets"}
    assert (preds["backend"] == "statsforecast").all()
    assert (preds["run_id"] == "r1").all()
    assert len(preds) == 24 * 2  # h steps x 2 models
    assert adapter.timing["fit_seconds"] >= 0.0


def test_cross_validation_produces_backtest_contract_and_horizon() -> None:
    adapter = StatsForecastAdapter(df=_df(), built_models=_built(), freq="1h", run_id="r1")
    bt = adapter.cross_validation(h=24, n_windows=3, step_size=24)
    assert list(bt.columns) == BACKTEST_PREDICTIONS_COLUMNS
    assert set(bt["horizon"]) == set(range(1, 25))
    # each (unique_id, cutoff) window carries h steps x n_models rows
    counts = bt.groupby(["unique_id", "cutoff"]).size()
    assert (counts == 24 * 2).all()
    assert adapter.timing["cross_validation_seconds"] >= 0.0


def test_model_types_exposed() -> None:
    adapter = StatsForecastAdapter(df=_df(), built_models=_built(), freq="1h", run_id="r1")
    assert adapter.model_types == {"seasonal_naive": "naive", "auto_ets": "ets"}
