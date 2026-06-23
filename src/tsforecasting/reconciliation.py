"""Hierarchical reconciliation core (P9).

Independent of the MVP-0 ``run_pipeline``. Produces the three P9 artifacts'
worth of long frames: base forecasts (pre-reconciliation), reconciled forecasts
(one row per node x step x reconciler), and per-(base_model x reconciler)
diagnostics (coherence flag + mse vs hold-out).

Reconcilers are resolved from the config's ``{class, params}`` spec via
importlib (mirroring MLForecast's target-transform resolution), so no
reconciler registry is needed. ``hierarchicalforecast`` is imported lazily so
this module is only pulled in on the ``reconcile`` code path.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd
from statsforecast import StatsForecast

from tsforecasting.artifacts.schema import (
    BASE_PREDICTIONS_COLUMNS,
    RECONCILED_PREDICTIONS_COLUMNS,
    RECONCILIATION_DIAGNOSTICS_COLUMNS,
)
from tsforecasting.config.hierarchical import ReconcilerSpec
from tsforecasting.models.registry import BuiltModel

_COHERENCE_ATOL = 1e-6


def _resolve_reconciler(spec: ReconcilerSpec) -> Any:
    """Instantiate a reconciler from its ``{class_path, params}`` spec."""
    module_path, _, cls_name = spec.class_path.rpartition(".")
    if not module_path or not cls_name:
        raise ValueError(f"invalid reconciler class path '{spec.class_path}'")
    cls = getattr(importlib.import_module(module_path), cls_name)
    return cls(**spec.params)


def _bottom_ids(tags: dict) -> list[str]:
    """Deepest hierarchy level = the tag with the most unique_ids."""
    deepest = max(tags, key=lambda k: len(tags[k]))
    return list(tags[deepest])


def _coherence(
    Y_rec: pd.DataFrame, col: str, S_mat: pd.DataFrame, bottom_ids: list[str]
) -> bool:
    """True iff reconciled nodes equal S @ reconciled bottom (within atol).

    ``S_mat`` is the summation matrix indexed by node id with bottom-series
    columns (already reordered to ``bottom_ids``).
    """
    max_err = 0.0
    for ds_val in Y_rec["ds"].unique():
        sub = Y_rec[Y_rec["ds"] == ds_val].set_index("unique_id")
        y_rec = sub[col].reindex(S_mat.index).to_numpy(dtype=float)
        y_bottom = sub.loc[bottom_ids, col].to_numpy(dtype=float)
        recon = S_mat.to_numpy(dtype=float) @ y_bottom
        max_err = max(max_err, float(np.max(np.abs(y_rec - recon))))
    return max_err < _COHERENCE_ATOL


def _mse_vs_test(Y_rec: pd.DataFrame, col: str, test: pd.DataFrame) -> float:
    """Mean squared error of a reconciled column vs the hold-out ``test`` y."""
    left = Y_rec[["unique_id", "ds", col]].copy()
    left["ds"] = pd.to_datetime(left["ds"])
    right = test[["unique_id", "ds", "y"]].copy()
    right["ds"] = pd.to_datetime(right["ds"])
    merged = left.merge(right, on=["unique_id", "ds"], how="inner")
    if merged.empty:
        return float("nan")
    err = merged[col].to_numpy(dtype=float) - merged["y"].to_numpy(dtype=float)
    return float(np.mean(err**2))


def reconcile_pipeline(
    *,
    train: pd.DataFrame,
    test: pd.DataFrame,
    built_models: list[BuiltModel],
    freq: str,
    horizon: int,
    reconciler_specs: list[ReconcilerSpec],
    S_df: pd.DataFrame,
    tags: dict,
    run_id: str,
    diagnostics: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Base-forecast -> reconcile -> diagnostics.

    Returns ``(base_predictions, reconciled_predictions, reconciliation_diagnostics)``
    as long/summary frames matching the P9 artifact contracts.
    """
    from hierarchicalforecast.core import HierarchicalReconciliation

    # 1. base forecasts (wide): unique_id, ds, <one col per base model>
    sf = StatsForecast(models=[m.instance for m in built_models], freq=freq)
    Y_hat = sf.forecast(df=train, h=horizon)
    base_cols = [c for c in Y_hat.columns if c not in ("unique_id", "ds")]
    if len(base_cols) != len(built_models):
        raise ValueError(
            f"base model column count {len(base_cols)} != built models {len(built_models)}"
        )
    base_name_map = {base_cols[i]: built_models[i].name for i in range(len(base_cols))}

    # 2. base_predictions (long)
    base_long = Y_hat.melt(
        id_vars=["unique_id", "ds"],
        value_vars=base_cols,
        var_name="_bcol",
        value_name="yhat",
    )
    base_long["model"] = base_long["_bcol"].map(base_name_map)
    base_long["run_id"] = run_id
    base_long = base_long[list(BASE_PREDICTIONS_COLUMNS)]

    # summation matrix nodes x bottom, columns reordered to the bottom order
    bottom_ids = _bottom_ids(tags)
    S_mat = S_df.set_index("unique_id")[bottom_ids]

    rec_parts: list[pd.DataFrame] = []
    diag_rows: list[dict] = []
    for spec in reconciler_specs:
        reconciler = _resolve_reconciler(spec)
        hrec = HierarchicalReconciliation(reconcilers=[reconciler])
        Y_rec = hrec.reconcile(
            Y_hat_df=Y_hat,
            S_df=S_df,
            tags=tags,
            Y_df=train,
            diagnostics=diagnostics,
        )
        rec_cols = [
            c for c in Y_rec.columns if c not in ("unique_id", "ds") and c not in base_cols
        ]

        for rc in rec_cols:
            base_alias = rc.split("/", 1)[0]
            base_name = base_name_map[base_alias]
            part = Y_rec[["unique_id", "ds", rc]].rename(columns={rc: "yhat"})
            part["base_model"] = base_name
            part["reconciler"] = spec.name
            part["run_id"] = run_id
            rec_parts.append(part[list(RECONCILED_PREDICTIONS_COLUMNS)])

        # diagnostics per base model for this reconciler
        for base_alias, base_name in base_name_map.items():
            rc = next(
                (c for c in rec_cols if c.startswith(base_alias + "/")), None
            )
            if rc is None:
                continue
            coherent = _coherence(Y_rec, rc, S_mat, bottom_ids)
            mse_val = _mse_vs_test(Y_rec, rc, test)
            diag_rows.append(
                {
                    "run_id": run_id,
                    "base_model": base_name,
                    "reconciler": spec.name,
                    "coherent": bool(coherent),
                    "mse": mse_val,
                }
            )

    reconciled_long = (
        pd.concat(rec_parts, ignore_index=True) if rec_parts else pd.DataFrame(columns=RECONCILED_PREDICTIONS_COLUMNS)
    )
    diagnostics_df = pd.DataFrame(diag_rows, columns=RECONCILIATION_DIAGNOSTICS_COLUMNS)
    return base_long, reconciled_long, diagnostics_df
