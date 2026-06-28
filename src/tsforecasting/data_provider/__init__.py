"""标准数据加载和 Nixtla 长表契约。"""

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
    "load_data",
]
