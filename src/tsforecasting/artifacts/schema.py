"""Artifact column contracts and validation.

Field schemas are pinned to docs/unified-ts-framework-plan-v2.md §7. Each
contract lists the required columns; ``validate_columns`` asserts an artifact
DataFrame carries them before it is written to disk.
"""

from __future__ import annotations

import pandas as pd

PREDICTIONS_COLUMNS = ["unique_id", "ds", "yhat", "model", "backend", "run_id"]
BACKTEST_PREDICTIONS_COLUMNS = [
    "unique_id",
    "cutoff",
    "ds",
    "horizon",
    "y",
    "yhat",
    "model",
    "backend",
    "run_id",
]
METRICS_COLUMNS = ["run_id", "backend", "model", "metric", "value"]
RUNTIME_METRICS_COLUMNS = [
    "run_id",
    "backend",
    "model",
    "model_type",
    "n_series",
    "n_rows",
    "fit_seconds",
    "predict_seconds",
    "cross_validation_seconds",
    "total_seconds",
]
MODEL_COMPARISON_COLUMNS = [
    "run_id",
    "backend",
    "model",
    "model_type",
    "mae",
    "rmse",
    "mape",
    "smape",
    "total_seconds",
    "rank_metric",
    "rank",
]

ARTIFACT_CONTRACTS = {
    "predictions": PREDICTIONS_COLUMNS,
    "backtest_predictions": BACKTEST_PREDICTIONS_COLUMNS,
    "metrics": METRICS_COLUMNS,
    "runtime_metrics": RUNTIME_METRICS_COLUMNS,
    "model_comparison": MODEL_COMPARISON_COLUMNS,
}


class ArtifactError(ValueError):
    """Raised when an artifact DataFrame violates its column contract."""


def validate_columns(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Assert ``df`` has every required column for artifact ``name``."""
    expected = ARTIFACT_CONTRACTS.get(name)
    if expected is None:
        raise ArtifactError(f"unknown artifact contract '{name}'")
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ArtifactError(f"{name}: missing required columns {missing}")
    return df
