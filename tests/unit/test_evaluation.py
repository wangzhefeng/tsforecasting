"""Tests for evaluation metrics, incl. Phase-2 interval coverage/width."""

from __future__ import annotations

import pandas as pd

from tsforecasting.evaluation.metrics import compute_metrics


def _backtest_with_intervals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unique_id": ["s"] * 4,
            "cutoff": pd.to_datetime(["2024-01-01"] * 4),
            "ds": pd.to_datetime(
                ["2024-01-02", "2024-01-03", "2024-01-02", "2024-01-03"]
            ),
            "y": [1.0, 3.0, 1.0, 2.0],
            "yhat": [1.1, 1.9, 1.1, 1.9],
            "lo-80": [0.5, 1.5, 0.5, 1.5],
            "hi-80": [1.5, 2.5, 1.5, 2.5],
            "model": ["m", "m", "n", "n"],
            "backend": ["statsforecast"] * 4,
        }
    )


def test_compute_metrics_emits_core_metrics() -> None:
    m = compute_metrics(_backtest_with_intervals(), "r1")
    assert {"mae", "rmse", "mape", "smape"} <= set(m["metric"])


def test_compute_metrics_emits_interval_coverage_and_width() -> None:
    m = compute_metrics(_backtest_with_intervals(), "r1")
    metrics = set(m["metric"])
    assert "coverage-80" in metrics
    assert "width-80" in metrics
    # model m: y=[1,2] within [0.5,1.5] / [1.5,2.5] -> 1 of 2 inside -> coverage 0.5
    cov_m = m[(m["model"] == "m") & (m["metric"] == "coverage-80")]["value"].iloc[0]
    assert cov_m == 0.5
    # width = mean(hi - lo) = 1.0
    width_m = m[(m["model"] == "m") & (m["metric"] == "width-80")]["value"].iloc[0]
    assert width_m == 1.0


def test_model_comparison_appends_interval_columns() -> None:
    from tsforecasting.evaluation.metrics import build_model_comparison

    metrics = pd.DataFrame(
        [
            {"run_id": "r", "backend": "statsforecast", "model": "m", "metric": "mae", "value": 1.0},
            {"run_id": "r", "backend": "statsforecast", "model": "m", "metric": "rmse", "value": 1.2},
            {"run_id": "r", "backend": "statsforecast", "model": "m", "metric": "mape", "value": 0.1},
            {"run_id": "r", "backend": "statsforecast", "model": "m", "metric": "smape", "value": 0.08},
            {"run_id": "r", "backend": "statsforecast", "model": "m", "metric": "coverage-80", "value": 0.9},
            {"run_id": "r", "backend": "statsforecast", "model": "m", "metric": "width-80", "value": 2.0},
        ]
    )
    runtime = pd.DataFrame(
        [{"run_id": "r", "backend": "statsforecast", "model": "m", "model_type": "naive", "total_seconds": 0.1}]
    )
    comp = build_model_comparison(metrics, runtime, rank_metric="mae")
    # core columns still present and ordered
    assert list(comp.columns)[:4] == ["run_id", "backend", "model", "model_type"]
    # interval columns appended for display
    assert "coverage-80" in comp.columns
    assert "width-80" in comp.columns
    assert comp.iloc[0]["coverage-80"] == 0.9
    # ranking still by the core point metric
    assert comp.iloc[0]["rank_metric"] == "mae"
