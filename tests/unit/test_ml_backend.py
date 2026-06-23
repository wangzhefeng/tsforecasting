"""Tests for the MLForecast backend adapter output contracts.

Mirrors ``test_stats_backend.py``. Skipped entirely when the ``ml`` extra
(``mlforecast``) is not installed, so the base dependency set still passes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("mlforecast")

from tsforecasting.artifacts import (  # noqa: E402
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.config import MLForecastConfig, ModelConfig  # noqa: E402
from tsforecasting.models import build_model  # noqa: E402
from tsforecasting.models.nixtla.ml import MLForecastAdapter  # noqa: E402


def _df(n: int = 240) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="1h")
    y = np.sin(2 * np.pi * np.arange(n) / 24.0)  # period 24 -> lags include 24
    return pd.DataFrame({"unique_id": "s0", "ds": idx, "y": y})


def _built() -> list:
    return [
        build_model(ModelConfig(name="linear_regression", backend="mlforecast", params={})),
        build_model(ModelConfig(name="ridge", backend="mlforecast", params={"alpha": 0.5})),
    ]


def _cfg(
    *,
    target_transforms: list[dict] | None = None,
) -> MLForecastConfig:
    return MLForecastConfig(
        lags=[1, 24],
        date_features=["hour"],
        target_transforms=target_transforms,
    )


def test_predict_produces_predictions_contract() -> None:
    adapter = MLForecastAdapter(
        df=_df(), built_models=_built(), freq="1h", run_id="r1", mlforecast_config=_cfg()
    )
    preds = adapter.predict(h=24)
    assert list(preds.columns) == PREDICTIONS_COLUMNS
    assert set(preds["model"]) == {"linear_regression", "ridge"}
    assert (preds["backend"] == "mlforecast").all()
    assert (preds["run_id"] == "r1").all()
    assert len(preds) == 24 * 2  # h steps x 2 models
    assert adapter.timing["fit_seconds"] >= 0.0
    assert adapter.timing["predict_seconds"] >= 0.0


def test_cross_validation_produces_backtest_contract_and_horizon() -> None:
    adapter = MLForecastAdapter(
        df=_df(), built_models=_built(), freq="1h", run_id="r1", mlforecast_config=_cfg()
    )
    bt = adapter.cross_validation(h=24, n_windows=3, step_size=24)
    assert list(bt.columns) == BACKTEST_PREDICTIONS_COLUMNS
    assert set(bt["horizon"]) == set(range(1, 25))
    # each (unique_id, cutoff) window carries h steps x n_models rows
    counts = bt.groupby(["unique_id", "cutoff"]).size()
    assert (counts == 24 * 2).all()
    assert adapter.timing["cross_validation_seconds"] >= 0.0


def test_model_types_exposed() -> None:
    adapter = MLForecastAdapter(
        df=_df(), built_models=_built(), freq="1h", run_id="r1", mlforecast_config=_cfg()
    )
    assert adapter.model_types == {"linear_regression": "linear", "ridge": "ridge"}


def test_target_transforms_resolve_and_preserve_contract() -> None:
    cfg = _cfg(
        target_transforms=[{"class": "mlforecast.target_transforms.Differences", "args": [[24]]}]
    )
    adapter = MLForecastAdapter(
        df=_df(), built_models=_built(), freq="1h", run_id="r1", mlforecast_config=cfg
    )
    preds = adapter.predict(h=24)
    bt = adapter.cross_validation(h=24, n_windows=3, step_size=24)
    assert list(preds.columns) == PREDICTIONS_COLUMNS
    assert list(bt.columns) == BACKTEST_PREDICTIONS_COLUMNS
    assert set(bt["horizon"]) == set(range(1, 25))


def test_predict_with_levels_appends_interval_columns() -> None:
    # MLForecast conformal intervals apply to predict (future), not cross_validation.
    adapter = MLForecastAdapter(
        df=_df(), built_models=_built(), freq="1h", run_id="r1",
        mlforecast_config=_cfg(), levels=[80, 95],
    )
    preds = adapter.predict(h=24)
    assert list(preds.columns)[: len(PREDICTIONS_COLUMNS)] == list(PREDICTIONS_COLUMNS)
    assert {"lo-80", "hi-80", "lo-95", "hi-95"} <= set(preds.columns)
    for level in (80, 95):
        assert (preds[f"lo-{level}"] <= preds["yhat"]).all()
        assert (preds["yhat"] <= preds[f"hi-{level}"]).all()
