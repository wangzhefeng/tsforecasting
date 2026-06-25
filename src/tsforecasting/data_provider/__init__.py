"""Canonical data loading and the Nixtla long-table contract."""

from tsforecasting.data_provider.hierarchical import (
    LoadedHierarchical,
    load_hierarchical,
)
from tsforecasting.data_provider.loader import (
    DEFAULT_UNIQUE_ID,
    DataError,
    LoadedData,
    load_data,
)

__all__ = [
    "DEFAULT_UNIQUE_ID",
    "DataError",
    "LoadedData",
    "LoadedHierarchical",
    "load_data",
    "load_hierarchical",
]
