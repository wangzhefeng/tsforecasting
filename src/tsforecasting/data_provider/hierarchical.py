"""Hierarchical dataset loading (P9).

Loads a grouped hierarchical dataset (MVP: TourismSmall via ``datasetsforecast``)
into the Nixtla ``Y_df / S_df / tags`` triple, with ``S_df`` reshaped so its node
ids live in a ``unique_id`` column (the shape ``HierarchicalReconciliation``
expects). ``datasetsforecast`` is imported lazily so the base package stays
importable without the ``hierarchical`` extra.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

import pandas as pd

from tsforecasting.config.hierarchical import HierarchicalDataConfig
from tsforecasting.data_provider.loader import DataError


@dataclass
class LoadedHierarchical:
    """Hierarchical triple plus metadata for the manifest."""

    Y_df: pd.DataFrame
    S_df: pd.DataFrame
    tags: dict
    meta: dict[str, Any]


def load_hierarchical(data: HierarchicalDataConfig) -> LoadedHierarchical:
    """Load ``Y_df / S_df / tags`` for a datasetsforecast hierarchical group."""
    if data.source != "datasetsforecast":
        raise DataError(f"data.source '{data.source}' not supported")
    from datasetsforecast.hierarchical import HierarchicalData

    # Signature advertises (Y_df, S_df) but the call returns 3 values incl. tags.
    Y_df, S_df, tags = HierarchicalData.load(data.cache_dir, group=data.dataset)
    # Node ids come back in the S_df index; reconcile() needs a unique_id column.
    if "unique_id" not in S_df.columns:
        S_df = S_df.reset_index(names="unique_id")
    meta = {
        "source": data.source,
        "dataset": data.dataset,
        "freq": data.freq,
        "cache_dir": data.cache_dir,
        "n_series": int(Y_df["unique_id"].nunique()),
        "n_rows": int(len(Y_df)),
        "levels": OrderedDict((k, len(v)) for k, v in tags.items()),
    }
    return LoadedHierarchical(Y_df=Y_df, S_df=S_df, tags=tags, meta=meta)
