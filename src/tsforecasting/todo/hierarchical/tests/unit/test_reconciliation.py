"""Tests for the reconciliation core (P9).

Uses a tiny synthetic hierarchy (total = b1 + b2) so the reconcile + diagnostics
logic is exercised without downloading TourismSmall. Skipped entirely when the
``hierarchical`` extra is not installed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("hierarchicalforecast")

from tsforecasting.artifacts import (  # noqa: E402
    BASE_PREDICTIONS_COLUMNS,
    RECONCILED_PREDICTIONS_COLUMNS,
    RECONCILIATION_DIAGNOSTICS_COLUMNS,
)
from tsforecasting.config import ModelConfig  # noqa: E402
from tsforecasting.config.hierarchical import ReconcilerSpec  # noqa: E402
from tsforecasting.models import build_model  # noqa: E402
from tsforecasting.reconciliation import reconcile_pipeline  # noqa: E402


def _toy_hierarchy(n: int = 8, horizon: int = 2):
    """Synthetic 2-level hierarchy: ``total = b1 + b2``."""
    ds = pd.date_range("2024-03-31", periods=n, freq="QE")
    b1 = np.arange(n, dtype=float)
    b2 = np.arange(n, dtype=float) * 2.0
    total = b1 + b2
    rows = []
    for name, y in (("total", total), ("b1", b1), ("b2", b2)):
        for i in range(n):
            rows.append({"unique_id": name, "ds": ds[i], "y": y[i]})
    Y_df = pd.DataFrame(rows)
    S_df = pd.DataFrame(
        {"b1": [1, 1, 0], "b2": [1, 0, 1]}, index=["total", "b1", "b2"]
    ).reset_index(names="unique_id")
    tags = {"Total": np.array(["total"]), "Bottom": np.array(["b1", "b2"])}
    last = sorted(Y_df["ds"].unique())[-horizon:]
    train = Y_df[~Y_df["ds"].isin(last)].copy()
    test = Y_df[Y_df["ds"].isin(last)].copy()
    return train, test, S_df, tags


def _models() -> list:
    return [
        build_model(
            ModelConfig(
                name="seasonal_naive", backend="statsforecast", params={"season_length": 2}
            )
        )
    ]


def _specs() -> list[ReconcilerSpec]:
    return [
        ReconcilerSpec(name="bottom_up", class_path="hierarchicalforecast.methods.BottomUp", params={}),
        ReconcilerSpec(
            name="min_trace_ols",
            class_path="hierarchicalforecast.methods.MinTrace",
            params={"method": "ols"},
        ),
    ]


def test_reconcile_pipeline_artifact_contracts() -> None:
    train, test, S_df, tags = _toy_hierarchy()
    base_long, rec_long, diag = reconcile_pipeline(
        train=train,
        test=test,
        built_models=_models(),
        freq="QE",
        horizon=2,
        reconciler_specs=_specs(),
        S_df=S_df,
        tags=tags,
        run_id="r1",
    )
    assert list(base_long.columns) == BASE_PREDICTIONS_COLUMNS
    assert list(rec_long.columns) == RECONCILED_PREDICTIONS_COLUMNS
    assert list(diag.columns) == RECONCILIATION_DIAGNOSTICS_COLUMNS


def test_reconcile_pipeline_content() -> None:
    train, test, S_df, tags = _toy_hierarchy()
    base_long, rec_long, diag = reconcile_pipeline(
        train=train,
        test=test,
        built_models=_models(),
        freq="QE",
        horizon=2,
        reconciler_specs=_specs(),
        S_df=S_df,
        tags=tags,
        run_id="r1",
    )
    # base: 3 nodes x 2 horizon x 1 model
    assert len(base_long) == 3 * 2 * 1
    assert set(base_long["model"]) == {"seasonal_naive"}
    # reconciled: 3 nodes x 2 horizon x 2 reconcilers
    assert len(rec_long) == 3 * 2 * 2
    assert set(rec_long["reconciler"]) == {"bottom_up", "min_trace_ols"}
    assert set(rec_long["base_model"]) == {"seasonal_naive"}
    # diagnostics: 1 base model x 2 reconcilers
    assert len(diag) == 2
    assert set(diag["reconciler"]) == {"bottom_up", "min_trace_ols"}
    # reconciled forecasts must be coherent by construction
    assert (diag["coherent"] == True).all()  # noqa: E712
    # mse is a finite non-negative number per row
    assert np.isfinite(diag["mse"]).all()
    assert (diag["mse"] >= 0).all()
