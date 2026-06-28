"""Artifact 列契约和写入前校验。

字段 schema 与方案文档中的 artifact 契约保持一致。每个契约只声明必需列；
``validate_columns`` 在写 CSV 前检查这些列是否存在，避免产物静默漂移。
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
    """artifact DataFrame 不满足列契约时抛出。"""


def validate_columns(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """确认指定 artifact 的必需列都存在；允许额外列用于向后兼容扩展。"""
    expected = ARTIFACT_CONTRACTS.get(name)
    if expected is None:
        raise ArtifactError(f"unknown artifact contract '{name}'")
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ArtifactError(f"{name}: missing required columns {missing}")
    return df
