"""Tests for the P9 hierarchical reconciliation path.

Contract + config tests run in the base env (pure schema, no extras). The
reconciliation / smoke tests ``importorskip`` the ``hierarchical`` extra.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from tsforecasting.artifacts import (
    ARTIFACT_CONTRACTS,
    ArtifactError,
    validate_columns,
)

# --- artifact contracts (base env) ----------------------------------------


def test_hierarchical_artifact_contracts_registered() -> None:
    for name in (
        "base_predictions",
        "reconciled_predictions",
        "reconciliation_diagnostics",
    ):
        assert name in ARTIFACT_CONTRACTS, name


def test_base_predictions_columns() -> None:
    assert ARTIFACT_CONTRACTS["base_predictions"] == [
        "unique_id",
        "ds",
        "yhat",
        "model",
        "run_id",
    ]


def test_reconciled_predictions_columns() -> None:
    assert ARTIFACT_CONTRACTS["reconciled_predictions"] == [
        "unique_id",
        "ds",
        "yhat",
        "base_model",
        "reconciler",
        "run_id",
    ]


def test_reconciliation_diagnostics_columns() -> None:
    assert ARTIFACT_CONTRACTS["reconciliation_diagnostics"] == [
        "run_id",
        "base_model",
        "reconciler",
        "coherent",
        "mse",
    ]


def test_validate_columns_accepts_reconciled_frame() -> None:
    df = pd.DataFrame(
        {
            "unique_id": ["a"],
            "ds": [pd.Timestamp("2024-01-01")],
            "yhat": [1.0],
            "base_model": ["seasonal_naive"],
            "reconciler": ["bottom_up"],
            "run_id": ["r1"],
        }
    )
    validate_columns(df, "reconciled_predictions")


def test_validate_columns_rejects_missing_diagnostic_col() -> None:
    df = pd.DataFrame({"run_id": ["r1"], "base_model": ["m"], "reconciler": ["b"]})
    with pytest.raises(ArtifactError, match="reconciliation_diagnostics"):
        validate_columns(df, "reconciliation_diagnostics")


# --- hierarchical config (base env) ---------------------------------------


def _base_hierarchical() -> dict:
    return {
        "data": {
            "source": "datasetsforecast",
            "dataset": "TourismSmall",
            "freq": "QE",
        },
        "base_forecast": {
            "backend": "statsforecast",
            "horizon": 4,
            "models": [{"name": "seasonal_naive", "params": {"season_length": 4}}],
        },
        "hierarchical": {
            "reconcilers": [
                {"name": "bottom_up", "class": "hierarchicalforecast.methods.BottomUp", "params": {}},
            ],
            "diagnostics": True,
        },
        "evaluation": {"metrics": ["mse"]},
        "runtime": {"log_name": "tourism_small_hierarchical", "log_level": "INFO"},
        "artifacts": {"output_dir": "results/tourism_small_hierarchical"},
        "seed": 0,
    }


def _write_cfg(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "hier.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_hierarchical_config_loads() -> None:
    from tsforecasting.config.hierarchical import load_hierarchical_config

    config = load_hierarchical_config(_write_cfg(Path("/tmp"), _base_hierarchical()))
    assert config.data.source == "datasetsforecast"
    assert config.data.dataset == "TourismSmall"
    assert config.data.freq == "QE"
    assert config.base_forecast.backend == "statsforecast"
    assert config.base_forecast.horizon == 4
    assert [m.name for m in config.base_forecast.models] == ["seasonal_naive"]
    assert config.base_forecast.models[0].backend == "statsforecast"
    assert config.hierarchical.reconcilers[0].name == "bottom_up"
    assert config.hierarchical.reconcilers[0].class_path == "hierarchicalforecast.methods.BottomUp"
    assert config.hierarchical.diagnostics is True
    assert config.evaluation.metrics == ["mse"]


def test_hierarchical_config_bad_source_raises(tmp_path: Path) -> None:
    from tsforecasting.config.hierarchical import ConfigError, load_hierarchical_config

    data = _base_hierarchical()
    data["data"]["source"] = "csv"
    with pytest.raises(ConfigError, match="source"):
        load_hierarchical_config(_write_cfg(tmp_path, data))


def test_hierarchical_config_bad_base_backend_raises(tmp_path: Path) -> None:
    from tsforecasting.config.hierarchical import ConfigError, load_hierarchical_config

    data = _base_hierarchical()
    data["base_forecast"]["backend"] = "mlforecast"
    with pytest.raises(ConfigError, match="backend"):
        load_hierarchical_config(_write_cfg(tmp_path, data))


def test_hierarchical_config_bad_metric_raises(tmp_path: Path) -> None:
    from tsforecasting.config.hierarchical import ConfigError, load_hierarchical_config

    data = _base_hierarchical()
    data["evaluation"]["metrics"] = ["mae"]
    with pytest.raises(ConfigError, match="metric"):
        load_hierarchical_config(_write_cfg(tmp_path, data))


def test_hierarchical_config_reconciler_dup_name_raises(tmp_path: Path) -> None:
    from tsforecasting.config.hierarchical import ConfigError, load_hierarchical_config

    data = _base_hierarchical()
    data["hierarchical"]["reconcilers"].append(
        {"name": "bottom_up", "class": "hierarchicalforecast.methods.MinTrace", "params": {"method": "ols"}}
    )
    with pytest.raises(ConfigError, match="duplicate"):
        load_hierarchical_config(_write_cfg(tmp_path, data))


def test_hierarchical_config_nonpos_horizon_raises(tmp_path: Path) -> None:
    from tsforecasting.config.hierarchical import ConfigError, load_hierarchical_config

    data = _base_hierarchical()
    data["base_forecast"]["horizon"] = 0
    with pytest.raises(ConfigError, match="horizon"):
        load_hierarchical_config(_write_cfg(tmp_path, data))
