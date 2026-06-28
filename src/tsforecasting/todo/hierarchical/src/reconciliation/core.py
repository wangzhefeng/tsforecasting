"""层级协调核心：基础预测、reconcile、诊断表组装。"""

from __future__ import annotations

import pandas as pd
from statsforecast import StatsForecast

from tsforecasting.artifacts.schema import (
    BASE_PREDICTIONS_COLUMNS,
    RECONCILED_PREDICTIONS_COLUMNS,
    RECONCILIATION_DIAGNOSTICS_COLUMNS,
)
from tsforecasting.config.hierarchical import ReconcilerSpec
from tsforecasting.models.registry import BuiltModel
from tsforecasting.reconciliation.diagnostics import (
    bottom_ids,
    is_coherent,
    mse_vs_test,
)
from tsforecasting.reconciliation.resolvers import resolve_reconciler


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
    """执行基础预测、层级协调和诊断计算，返回三张标准 artifact 表。"""
    from hierarchicalforecast.core import HierarchicalReconciliation

    sf = StatsForecast(models=[m.instance for m in built_models], freq=freq)
    Y_hat = sf.forecast(df=train, h=horizon)
    base_cols = [c for c in Y_hat.columns if c not in ("unique_id", "ds")]
    if len(base_cols) != len(built_models):
        raise ValueError(
            f"base model column count {len(base_cols)} != built models {len(built_models)}"
        )
    base_name_map = {base_cols[i]: built_models[i].name for i in range(len(base_cols))}

    # 基础预测先转成长表，作为 base_predictions.csv 的直接来源。
    base_long = Y_hat.melt(
        id_vars=["unique_id", "ds"],
        value_vars=base_cols,
        var_name="_bcol",
        value_name="yhat",
    )
    base_long["model"] = base_long["_bcol"].map(base_name_map)
    base_long["run_id"] = run_id
    base_long = base_long[list(BASE_PREDICTIONS_COLUMNS)]

    bottom_series = bottom_ids(tags)
    S_mat = S_df.set_index("unique_id")[bottom_series]

    # 每个 reconciler 独立运行；上游输出列名通常是 "<base>/<reconciler>"。
    rec_parts: list[pd.DataFrame] = []
    diag_rows: list[dict] = []
    for spec in reconciler_specs:
        reconciler = resolve_reconciler(spec)
        hrec = HierarchicalReconciliation(reconcilers=[reconciler])
        Y_rec = hrec.reconcile(
            Y_hat_df=Y_hat,
            S_df=S_df,
            tags=tags,
            Y_df=train,
            diagnostics=diagnostics,
        )
        rec_cols = [
            c
            for c in Y_rec.columns
            if c not in ("unique_id", "ds") and c not in base_cols
        ]

        for rc in rec_cols:
            base_alias = rc.split("/", 1)[0]
            base_name = base_name_map[base_alias]
            part = Y_rec[["unique_id", "ds", rc]].rename(columns={rc: "yhat"})
            part["base_model"] = base_name
            part["reconciler"] = spec.name
            part["run_id"] = run_id
            rec_parts.append(part[list(RECONCILED_PREDICTIONS_COLUMNS)])

        for base_alias, base_name in base_name_map.items():
            rc = next((c for c in rec_cols if c.startswith(base_alias + "/")), None)
            if rc is None:
                continue
            diag_rows.append(
                {
                    "run_id": run_id,
                    "base_model": base_name,
                    "reconciler": spec.name,
                    "coherent": bool(is_coherent(Y_rec, rc, S_mat, bottom_series)),
                    "mse": mse_vs_test(Y_rec, rc, test),
                }
            )

    reconciled_long = (
        pd.concat(rec_parts, ignore_index=True)
        if rec_parts
        else pd.DataFrame(columns=RECONCILED_PREDICTIONS_COLUMNS)
    )
    diagnostics_df = pd.DataFrame(diag_rows, columns=RECONCILIATION_DIAGNOSTICS_COLUMNS)
    return base_long, reconciled_long, diagnostics_df
