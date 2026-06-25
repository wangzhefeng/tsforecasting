"""Canonical data loader: CSV -> Nixtla long table (``unique_id / ds / y``).

Responsibilities (per docs/unified-ts-framework-plan-v2.md §5.1):

- Field mapping: ``time_col -> ds``, ``target_col -> y``, and ``id_col`` ->
  ``unique_id``. When ``id_col`` is null (single series), assign
  ``unique_id = "series_0"``.
- ``ds`` must be parseable to a timestamp.
- No duplicate ``ds`` under the same ``unique_id`` (error).
- ``freq`` must be explicitly configured or stably inferrable; otherwise error.
- Missing time points are reported (counted), never silently filled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from tsforecasting.config import DataConfig

DEFAULT_UNIQUE_ID = "series_0"


class DataError(ValueError):
    """Raised when input data violates the canonical contract."""


@dataclass
class LoadedData:
    """Canonical long table plus mapping/stats metadata for the manifest."""

    df: pd.DataFrame
    meta: dict[str, Any]


def load_data(data: DataConfig) -> LoadedData:
    """Load a CSV into the canonical ``unique_id / ds / y`` long table."""
    df = pd.read_csv(data.path)

    if data.time_col not in df.columns:
        raise DataError(f"data: time_col '{data.time_col}' not found in {data.path}")
    if data.target_col not in df.columns:
        raise DataError(f"data: target_col '{data.target_col}' not found in {data.path}")

    out = pd.DataFrame(index=range(len(df)))
    if data.id_col is None:
        out["unique_id"] = DEFAULT_UNIQUE_ID
    else:
        if data.id_col not in df.columns:
            raise DataError(f"data: id_col '{data.id_col}' not found in {data.path}")
        out["unique_id"] = df[data.id_col].astype(str).to_numpy()

    ds = pd.to_datetime(df[data.time_col], errors="raise")
    if ds.isna().any():
        raise DataError("data: time_col contains unparseable timestamps")
    out["ds"] = ds.to_numpy()
    out["y"] = df[data.target_col].to_numpy()

    dup_mask = out.duplicated(subset=["unique_id", "ds"], keep=False)
    if dup_mask.any():
        raise DataError(
            f"data: {int(dup_mask.sum())} rows have duplicate (unique_id, ds)"
        )

    out = out.sort_values(["unique_id", "ds"]).reset_index(drop=True)

    freq, inferred = _resolve_freq(out, data.freq)
    missing_points = _count_missing_points(out, freq)

    meta = {
        "path": str(data.path),
        "time_col": data.time_col,
        "target_col": data.target_col,
        "id_col": data.id_col,
        "freq": freq,
        "freq_inferred": inferred,
        "n_series": int(out["unique_id"].nunique()),
        "n_rows": int(len(out)),
        "missing_points": missing_points,
    }
    return LoadedData(df=out, meta=meta)


def _resolve_freq(df: pd.DataFrame, configured: str | None) -> tuple[str, bool]:
    if configured:
        return configured, False
    first_id = sorted(df["unique_id"].unique())[0]
    sample = df.loc[df["unique_id"] == first_id, "ds"].sort_values()
    inferred = pd.infer_freq(pd.DatetimeIndex(sample))
    if inferred is None:
        raise DataError(
            "data: freq is not configured and could not be inferred from ds"
        )
    return inferred, True


def _count_missing_points(df: pd.DataFrame, freq: str) -> int:
    total = 0
    for _, sub in df.groupby("unique_id"):
        sub = sub.sort_values("ds")
        full = pd.date_range(start=sub["ds"].min(), end=sub["ds"].max(), freq=freq)
        actual = pd.DatetimeIndex(sub["ds"])
        total += len(full.difference(actual))
    return total
