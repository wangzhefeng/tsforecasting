"""Evaluation: UtilsForecast metrics, runtime metrics, and model comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd
from utilsforecast.evaluation import evaluate
from utilsforecast.losses import mae, mape, rmse, smape

from tsforecasting.artifacts.schema import (
    METRICS_COLUMNS,
    MODEL_COMPARISON_COLUMNS,
    RUNTIME_METRICS_COLUMNS,
)
from tsforecasting.models.registry import BuiltModel

_METRIC_FNS = {"mae": mae, "rmse": rmse, "mape": mape, "smape": smape}
_CORE_METRICS = ["mae", "rmse", "mape", "smape"]


def compute_metrics(backtest: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """Compute the 4 core UtilsForecast metrics per model (long form).

    The contract fixes the core metrics as ``mae / rmse / mape / smape`` (v2
    "at least these four"); ``config.evaluation.metrics`` selects the ranking
    metric but all four are always produced.
    """
    wide = backtest.pivot(
        index=["unique_id", "cutoff", "ds", "y"], columns="model", values="yhat"
    ).reset_index()
    wide.columns.name = None
    model_cols = [c for c in wide.columns if c not in ("unique_id", "cutoff", "ds", "y")]

    eval_df = evaluate(
        wide,
        metrics=[_METRIC_FNS[m] for m in _CORE_METRICS],
        models=model_cols,
    )
    # eval_df: unique_id, cutoff, metric, <model cols>; average across windows+series
    agg = eval_df.groupby("metric")[model_cols].mean()

    backend_of = (
        backtest[["model", "backend"]]
        .drop_duplicates()
        .set_index("model")["backend"]
        .to_dict()
    )
    rows = []
    for metric in _CORE_METRICS:
        for model in model_cols:
            rows.append(
                {
                    "run_id": run_id,
                    "backend": backend_of[model],
                    "model": model,
                    "metric": metric,
                    "value": float(agg.loc[metric, model]),
                }
            )

    # optional interval metrics (coverage / width) when backtest carries lo/hi.
    # These are additive to metrics.csv but excluded from model_comparison,
    # which only pivots the four core metrics.
    levels = sorted({int(c.split("-", 1)[1]) for c in backtest.columns if c.startswith("lo-")})
    for level in levels:
        lo_col, hi_col = f"lo-{level}", f"hi-{level}"
        if lo_col not in backtest.columns or hi_col not in backtest.columns:
            continue
        for model in model_cols:
            sub = backtest[backtest["model"] == model]
            coverage = float(((sub[lo_col] <= sub["y"]) & (sub["y"] <= sub[hi_col])).mean())
            width = float((sub[hi_col] - sub[lo_col]).mean())
            rows.append(
                {
                    "run_id": run_id,
                    "backend": backend_of[model],
                    "model": model,
                    "metric": f"coverage-{level}",
                    "value": coverage,
                }
            )
            rows.append(
                {
                    "run_id": run_id,
                    "backend": backend_of[model],
                    "model": model,
                    "metric": f"width-{level}",
                    "value": width,
                }
            )
    return pd.DataFrame(rows, columns=METRICS_COLUMNS)


def build_runtime_metrics(
    run_id: str,
    built_models: list[BuiltModel],
    timings: dict[str, dict[str, float]],
    n_series: int,
    n_rows: int,
) -> pd.DataFrame:
    """Per-model runtime metrics.

    ``timings`` maps backend -> batch-shared timing dict (each adapter fits all
    of its models in one batched object, so timing is shared within a backend).
    """
    rows = []
    for b in built_models:
        timing = timings[b.backend]
        total = (
            timing["fit_seconds"]
            + timing["predict_seconds"]
            + timing["cross_validation_seconds"]
        )
        rows.append(
            {
                "run_id": run_id,
                "backend": b.backend,
                "model": b.name,
                "model_type": b.model_type,
                "n_series": n_series,
                "n_rows": n_rows,
                "fit_seconds": timing["fit_seconds"],
                "predict_seconds": timing["predict_seconds"],
                "cross_validation_seconds": timing["cross_validation_seconds"],
                "total_seconds": total,
            }
        )
    return pd.DataFrame(rows, columns=RUNTIME_METRICS_COLUMNS)


def build_model_comparison(
    metrics: pd.DataFrame,
    runtime_metrics: pd.DataFrame,
    rank_metric: str = "mae",
) -> pd.DataFrame:
    """Wide ranked summary: metrics pivot + total_seconds + rank by ``rank_metric``."""
    wide = metrics.pivot(
        index=["run_id", "backend", "model"], columns="metric", values="value"
    ).reset_index()
    wide.columns.name = None
    for m in _CORE_METRICS:
        if m not in wide.columns:
            wide[m] = float("nan")
    rm = runtime_metrics[["run_id", "backend", "model", "model_type", "total_seconds"]]
    comp = wide.merge(rm, on=["run_id", "backend", "model"])
    comp["rank_metric"] = rank_metric
    comp = comp.sort_values(rank_metric, ascending=True, kind="stable").reset_index(drop=True)
    comp["rank"] = np.arange(1, len(comp) + 1)
    # Append any interval metric columns (coverage-/width-) for display; ranking
    # still uses the core point rank_metric.
    interval_cols = [
        c for c in wide.columns if c.startswith("coverage-") or c.startswith("width-")
    ]
    return comp[MODEL_COMPARISON_COLUMNS + interval_cols]
