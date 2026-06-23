"""Tests for config schema loading, validation, run_id, and overrides."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tsforecasting.cli import main as cli_main
from tsforecasting.config import (
    ConfigError,
    generate_run_id,
    load_config,
    resolve_overrides,
)

EXAMPLE = Path("configs/examples/ett_small_stats.yaml")

_RUN_ID_RE = re.compile(r"^tsforecasting-\d{8}\d{6}-[0-9a-f]{8}$")


def _base() -> dict:
    return {
        "data": {
            "path": "examples/ett_small/ETTh1.csv",
            "time_col": "date",
            "target_col": "OT",
            "freq": "1h",
        },
        "backtest": {"horizon": 24, "n_windows": 3, "step_size": 24},
        "models": [
            {"name": "seasonal_naive", "backend": "statsforecast", "params": {"season_length": 24}},
            {"name": "auto_ets", "backend": "statsforecast", "params": {"season_length": 24}},
        ],
        "evaluation": {"metrics": ["mae", "rmse", "mape", "smape"], "rank_metric": "mae"},
        "runtime": {"collect_timing": True, "log_name": "ett_small_mvp0", "log_level": "INFO"},
        "artifacts": {"output_dir": "runs/ett_small_stats", "save_plots": False},
        "seed": 0,
    }


def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


def test_example_config_loads_and_validates() -> None:
    config = load_config(EXAMPLE)
    assert [m.name for m in config.models] == ["seasonal_naive", "auto_ets"]
    assert config.data.freq == "1h"
    assert config.data.id_col is None
    assert config.evaluation.rank_metric == "mae"
    assert config.predict is not None and config.predict.horizon == 24
    assert config.seed == 0
    assert config.config_source is not None


def test_missing_data_path_raises(tmp_path: Path) -> None:
    data = _base()
    data["data"].pop("path")
    with pytest.raises(ConfigError, match="data.*path"):
        load_config(_write(tmp_path, data))


def test_empty_models_raises(tmp_path: Path) -> None:
    data = _base()
    data["models"] = []
    with pytest.raises(ConfigError, match="models"):
        load_config(_write(tmp_path, data))


def test_duplicate_model_names_raise(tmp_path: Path) -> None:
    data = _base()
    data["models"][1]["name"] = "seasonal_naive"
    with pytest.raises(ConfigError, match="unique"):
        load_config(_write(tmp_path, data))


def test_unsupported_backend_raises(tmp_path: Path) -> None:
    data = _base()
    data["models"][0]["backend"] = "xgboost"
    with pytest.raises(ConfigError, match="backend"):
        load_config(_write(tmp_path, data))


def test_mlforecast_backend_requires_section(tmp_path: Path) -> None:
    data = _base()
    data["models"].append({"name": "linear_regression", "backend": "mlforecast", "params": {}})
    # mlforecast model but no top-level mlforecast section -> error
    with pytest.raises(ConfigError, match="mlforecast"):
        load_config(_write(tmp_path, data))


def test_mlforecast_section_loads(tmp_path: Path) -> None:
    data = _base()
    data["models"].append({"name": "linear_regression", "backend": "mlforecast", "params": {}})
    data["mlforecast"] = {"lags": [1, 24], "date_features": ["hour"]}
    config = load_config(_write(tmp_path, data))
    assert config.mlforecast is not None
    assert config.mlforecast.lags == [1, 24]
    assert config.mlforecast.date_features == ["hour"]


def test_mlforecast_empty_lags_raises(tmp_path: Path) -> None:
    data = _base()
    data["models"].append({"name": "linear_regression", "backend": "mlforecast", "params": {}})
    data["mlforecast"] = {"lags": []}
    with pytest.raises(ConfigError, match="lags"):
        load_config(_write(tmp_path, data))


def test_mlforecast_bad_target_transforms_raises(tmp_path: Path) -> None:
    data = _base()
    data["models"].append({"name": "linear_regression", "backend": "mlforecast", "params": {}})
    data["mlforecast"] = {"lags": [1], "target_transforms": [{"args": [1]}]}  # missing 'class'
    with pytest.raises(ConfigError, match="target_transforms"):
        load_config(_write(tmp_path, data))


def test_neuralforecast_backend_loads_without_top_level_section(tmp_path: Path) -> None:
    # Unlike mlforecast, neuralforecast carries its hyperparams per-model, so no
    # top-level section is required.
    data = _base()
    data["models"].append(
        {
            "name": "nhits",
            "backend": "neuralforecast",
            "params": {"h": 24, "input_size": 48, "max_steps": 5},
        }
    )
    config = load_config(_write(tmp_path, data))
    assert config.models[-1].backend == "neuralforecast"
    assert config.models[-1].params["h"] == 24


def test_unsupported_metric_raises(tmp_path: Path) -> None:
    data = _base()
    data["evaluation"]["metrics"] = ["mae", "mase"]
    with pytest.raises(ConfigError, match="unsupported"):
        load_config(_write(tmp_path, data))


def test_rank_metric_not_in_metrics_raises(tmp_path: Path) -> None:
    data = _base()
    data["evaluation"]["rank_metric"] = "mase"
    with pytest.raises(ConfigError, match="rank_metric"):
        load_config(_write(tmp_path, data))


def test_non_positive_backtest_horizon_raises(tmp_path: Path) -> None:
    data = _base()
    data["backtest"]["horizon"] = 0
    with pytest.raises(ConfigError, match="horizon"):
        load_config(_write(tmp_path, data))


def test_missing_config_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yaml")


def test_generate_run_id_format() -> None:
    run_id = generate_run_id()
    assert _RUN_ID_RE.match(run_id), run_id


def test_resolve_overrides_applies_cli_values(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, _base()))
    resolve_overrides(
        config,
        run_id="custom-run",
        output_dir="runs/x",
        log_name="ln",
        log_level="debug",
    )
    assert config.run_id == "custom-run"
    assert config.artifacts.output_dir == "runs/x"
    assert config.runtime.log_name == "ln"
    assert config.runtime.log_level == "DEBUG"


def test_resolve_overrides_defaults_run_id(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, _base()))
    resolve_overrides(config)
    assert config.run_id is not None and _RUN_ID_RE.match(config.run_id)


def test_cli_validate_config_valid_example(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli_main(["validate-config", "--config", str(EXAMPLE)]) == 0
    out = capsys.readouterr().out
    assert "config valid" in out
    assert "seasonal_naive" in out


def test_cli_validate_config_invalid_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = _base()
    data["models"][0]["backend"] = "xgboost"
    path = _write(tmp_path, data)
    assert cli_main(["validate-config", "--config", str(path)]) == 1
    err = capsys.readouterr().err
    assert "config invalid" in err
