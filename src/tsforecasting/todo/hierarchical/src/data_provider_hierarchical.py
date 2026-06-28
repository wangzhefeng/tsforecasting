"""层级数据集加载。

把 datasetsforecast 的层级数据加载成 Nixtla 生态使用的
``Y_df / S_df / tags`` 三元组，并把 ``S_df`` 的节点 id 调整到
``unique_id`` 列上。``datasetsforecast`` 延迟导入，保证未安装
``hierarchical`` extra 时基础包仍可 import。
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
    """层级三元组和写入 manifest 所需的元数据。"""

    Y_df: pd.DataFrame
    S_df: pd.DataFrame
    tags: dict
    meta: dict[str, Any]


def load_hierarchical(data: HierarchicalDataConfig) -> LoadedHierarchical:
    """读取 datasetsforecast 层级数据集，返回 ``Y_df / S_df / tags``。"""
    if data.source != "datasetsforecast":
        raise DataError(f"data.source '{data.source}' not supported")
    from datasetsforecast.hierarchical import HierarchicalData

    # 上游签名文档只写 (Y_df, S_df)，实际还会返回 tags。
    Y_df, S_df, tags = HierarchicalData.load(data.cache_dir, group=data.dataset)
    # 上游把节点 id 放在 S_df index；reconcile() 需要 unique_id 列。
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
