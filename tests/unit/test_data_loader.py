"""Tests for the canonical data loader (unique_id/ds/y contract)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tsforecasting.config import DataConfig
from tsforecasting.data import DataError, load_data

ETT = Path("examples/ett_small/ETTh1.csv")


def _write_csv(tmp_path: Path, df: pd.DataFrame) -> Path:
    p = tmp_path / "data.csv"
    df.to_csv(p, index=False)
    return p


def test_loads_ett1_to_long_table() -> None:
    loaded = load_data(
        DataConfig(path=str(ETT), time_col="date", target_col="OT", id_col=None, freq="1h")
    )
    assert list(loaded.df.columns) == ["unique_id", "ds", "y"]
    assert (loaded.df["unique_id"] == "series_0").all()
    assert loaded.meta["n_rows"] > 0
    assert loaded.meta["n_series"] == 1
    assert loaded.meta["freq"] == "1h"
    assert loaded.meta["freq_inferred"] is False
    assert loaded.meta["missing_points"] == 0  # ETTh1 is complete hourly
    assert pd.api.types.is_datetime64_any_dtype(loaded.df["ds"])


def test_null_id_col_assigns_series_0(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        pd.DataFrame(
            {"date": ["2024-01-01 00:00", "2024-01-01 01:00"], "OT": [1.0, 2.0]}
        ),
    )
    loaded = load_data(DataConfig(path=str(p), time_col="date", target_col="OT", freq="1h"))
    assert loaded.df["unique_id"].tolist() == ["series_0", "series_0"]


def test_custom_id_col_maps_to_unique_id(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        pd.DataFrame(
            {
                "date": ["2024-01-01 00:00", "2024-01-01 00:00"],
                "region": ["a", "b"],
                "OT": [1.0, 2.0],
            }
        ),
    )
    loaded = load_data(
        DataConfig(path=str(p), time_col="date", target_col="OT", id_col="region", freq="1h")
    )
    assert sorted(loaded.df["unique_id"].tolist()) == ["a", "b"]


def test_duplicate_timestamp_raises(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        pd.DataFrame(
            {"date": ["2024-01-01 00:00", "2024-01-01 00:00"], "OT": [1.0, 2.0]}
        ),
    )
    with pytest.raises(DataError, match="duplicate"):
        load_data(DataConfig(path=str(p), time_col="date", target_col="OT", freq="1h"))


def test_missing_freq_and_not_inferrable_raises(tmp_path: Path) -> None:
    # irregular timestamps -> infer_freq returns None
    p = _write_csv(
        tmp_path,
        pd.DataFrame(
            {
                "date": ["2024-01-01 00:00", "2024-01-01 00:05", "2024-01-03 09:30"],
                "OT": [1.0, 2.0, 3.0],
            }
        ),
    )
    with pytest.raises(DataError, match="freq"):
        load_data(DataConfig(path=str(p), time_col="date", target_col="OT", freq=None))


def test_missing_freq_inferred_when_regular(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        pd.DataFrame(
            {"date": ["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 02:00"], "OT": [1.0, 2.0, 3.0]}
        ),
    )
    loaded = load_data(DataConfig(path=str(p), time_col="date", target_col="OT", freq=None))
    assert loaded.meta["freq_inferred"] is True
    assert loaded.meta["freq"] is not None


def test_missing_points_reported_not_filled(tmp_path: Path) -> None:
    # hourly with one hour missing in the middle
    p = _write_csv(
        tmp_path,
        pd.DataFrame(
            {"date": ["2024-01-01 00:00", "2024-01-01 02:00"], "OT": [1.0, 3.0]}
        ),
    )
    loaded = load_data(DataConfig(path=str(p), time_col="date", target_col="OT", freq="1h"))
    assert loaded.meta["missing_points"] == 1
    assert len(loaded.df) == 2  # not filled


def test_missing_time_col_raises(tmp_path: Path) -> None:
    p = _write_csv(tmp_path, pd.DataFrame({"OT": [1.0, 2.0]}))
    with pytest.raises(DataError, match="time_col"):
        load_data(DataConfig(path=str(p), time_col="date", target_col="OT", freq="1h"))
