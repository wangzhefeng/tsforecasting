"""预测 adapter 共享的 DataFrame 归一化 helper。"""

from __future__ import annotations

import pandas as pd

NON_MODEL_COLS_FORECAST = ("unique_id", "ds")
NON_MODEL_COLS_CV = ("unique_id", "ds", "cutoff", "y")


def is_pure_model_col(col: str) -> bool:
    """判断列是否为点预测模型列，而不是 lo-/hi- 区间列。"""
    return "-lo-" not in col and "-hi-" not in col


def interval_columns(levels: list[int] | None) -> list[str]:
    """按 levels 生成 artifact 中追加的区间列顺序。"""
    out: list[str] = []
    if levels:
        for level in levels:
            out += [f"lo-{level}", f"hi-{level}"]
    return out


def melt_forecast_long(
    wide: pd.DataFrame,
    non_model_cols: tuple[str, ...],
    name_map: dict[str, str],
    levels: list[int] | None,
) -> pd.DataFrame:
    """把 Nixtla wide 预测/回测输出转换成统一长表契约。"""
    model_cols = [
        c for c in wide.columns if c not in non_model_cols and is_pure_model_col(c)
    ]
    if not levels:
        long = wide.melt(
            id_vars=list(non_model_cols),
            value_vars=model_cols,
            var_name="_model_col",
            value_name="yhat",
        )
        long["model"] = long["_model_col"].map(name_map)
        return long
    parts: list[pd.DataFrame] = []
    for mc in model_cols:
        cols = list(non_model_cols) + [mc]
        rename: dict[str, str] = {mc: "yhat"}
        for level in levels:
            lo, hi = f"{mc}-lo-{level}", f"{mc}-hi-{level}"
            cols += [lo, hi]
            rename[lo] = f"lo-{level}"
            rename[hi] = f"hi-{level}"
        sub = wide[cols].rename(columns=rename)
        sub["model"] = name_map[mc]
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


def add_dense_horizon(df: pd.DataFrame) -> pd.DataFrame:
    """在每个 ``(unique_id, cutoff)`` 回测窗口内按 ds 生成 dense horizon。"""
    df["horizon"] = (
        df.groupby(["unique_id", "cutoff"])["ds"].rank(method="dense").astype(int)
    )
    return df
