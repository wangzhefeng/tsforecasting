"""层级协调诊断 helper：底层节点、coherence 校验和 holdout MSE。"""

from __future__ import annotations

import numpy as np
import pandas as pd

_COHERENCE_ATOL = 1e-6


def bottom_ids(tags: dict) -> list[str]:
    """返回最底层节点：tags 中 unique_id 数量最多的层级。"""
    deepest = max(tags, key=lambda k: len(tags[k]))
    return list(tags[deepest])


def is_coherent(
    Y_rec: pd.DataFrame, col: str, S_mat: pd.DataFrame, bottom_series: list[str]
) -> bool:
    """检查协调后所有节点是否近似等于 ``S @ 底层节点预测``。"""
    max_err = 0.0
    for ds_val in Y_rec["ds"].unique():
        sub = Y_rec[Y_rec["ds"] == ds_val].set_index("unique_id")
        y_rec = sub[col].reindex(S_mat.index).to_numpy(dtype=float)
        y_bottom = sub.loc[bottom_series, col].to_numpy(dtype=float)
        recon = S_mat.to_numpy(dtype=float) @ y_bottom
        max_err = max(max_err, float(np.max(np.abs(y_rec - recon))))
    return max_err < _COHERENCE_ATOL


def mse_vs_test(Y_rec: pd.DataFrame, col: str, test: pd.DataFrame) -> float:
    """计算某个协调后预测列相对 holdout test.y 的均方误差。"""
    left = Y_rec[["unique_id", "ds", col]].copy()
    left["ds"] = pd.to_datetime(left["ds"])
    right = test[["unique_id", "ds", "y"]].copy()
    right["ds"] = pd.to_datetime(right["ds"])
    merged = left.merge(right, on=["unique_id", "ds"], how="inner")
    if merged.empty:
        return float("nan")
    err = merged[col].to_numpy(dtype=float) - merged["y"].to_numpy(dtype=float)
    return float(np.mean(err**2))
