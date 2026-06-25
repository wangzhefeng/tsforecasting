"""End-to-end smoke test: the MVP-0 StatsForecast vertical slice.

Artifacts are redirected to an absolute tmp ``--output-dir``; the example
config's relative ``data.path`` resolves from the repo root (pytest cwd). The
vendored logger writes to the gitignored repo-root ``logs/`` directory.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from tsforecasting.cli import main as cli_main
from tsforecasting.config import load_config, resolve_overrides
from tsforecasting.orchestration import run_pipeline

EXAMPLE = Path("configs/examples/ett_small/stats.yaml")
ML_EXAMPLE = Path("configs/examples/ett_small/ml.yaml")

_MANIFEST_KEYS = [
    "run_id",
    "run_id_rule",
    "config_source",
    "run_command",
    "seed",
    "per_backend_seed",
    "input",
    "field_mapping",
    "freq",
    "backtest",
    "models",
    "evaluation",
    "artifacts",
    "log_path",
    "env",
    "created_at_utc",
]


def test_run_pipeline_smoke(tmp_path: Path) -> None:
    config = load_config(EXAMPLE)
    resolve_overrides(config, run_id="smoke-test", output_dir=str(tmp_path / "results"))

    run_dir = run_pipeline(config, do_predict=True)

    assert run_dir == tmp_path / "results" / "smoke-test"
    for name in [
        "predictions.csv",
        "backtest_predictions.csv",
        "metrics.csv",
        "runtime_metrics.csv",
        "model_comparison.csv",
        "manifest.json",
        "run_config.yaml",
    ]:
        assert (run_dir / name).is_file(), name

    metrics = pd.read_csv(run_dir / "metrics.csv")
    assert set(metrics["metric"]) == {"mae", "rmse", "mape", "smape"}
    assert set(metrics["model"]) == {"seasonal_naive", "auto_ets"}

    comp = pd.read_csv(run_dir / "model_comparison.csv")
    assert list(comp["rank"]) == [1, 2]
    assert comp.sort_values("rank").iloc[0]["rank_metric"] == "mae"
    assert {"mae", "rmse", "mape", "smape"} <= set(comp.columns)

    runtime = pd.read_csv(run_dir / "runtime_metrics.csv")
    assert set(runtime["model_type"]) == {"naive", "ets"}

    manifest = json.loads((run_dir / "manifest.json").read_text())
    for key in _MANIFEST_KEYS:
        assert key in manifest, key
    assert manifest["run_id"] == "smoke-test"
    assert manifest["predict"] == {"horizon": 24}
    assert "predictions" in manifest["artifacts"]

    run_config = (run_dir / "run_config.yaml").read_text()
    assert "smoke-test" in run_config


def test_cli_run_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(
        [
            "run",
            "--config",
            str(EXAMPLE),
            "--run-id",
            "cli-test",
            "--output-dir",
            str(tmp_path / "results"),
        ]
    )
    assert rc == 0
    assert "run complete" in capsys.readouterr().out
    assert (tmp_path / "results" / "cli-test").is_dir()


def test_cli_dry_run_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(
        [
            "run",
            "--config",
            str(EXAMPLE),
            "--dry-run",
            "--run-id",
            "dry",
            "--output-dir",
            str(tmp_path / "results"),
        ]
    )
    assert rc == 0
    assert "dry-run plan" in capsys.readouterr().out
    assert not (tmp_path / "results").exists()


def test_cli_report_invalid_run_dir_fails_gracefully(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Works in any env: invalid run_dir -> detect_run_type ValueError; in base env
    # (no nbformat) the import error is also caught. Either way, graceful exit 1.
    rc = cli_main(["report", "--run-dir", str(tmp_path / "nonexistent")])
    assert rc == 1
    assert "report failed" in capsys.readouterr().err


def test_run_pipeline_ml_mixed_smoke(tmp_path: Path) -> None:
    """Mixed statsforecast + mlforecast run ranks both backends together."""
    pytest.importorskip("mlforecast")
    config = load_config(ML_EXAMPLE)
    resolve_overrides(config, run_id="ml-smoke-test", output_dir=str(tmp_path / "results"))

    run_dir = run_pipeline(config, do_predict=True)
    assert run_dir == tmp_path / "results" / "ml-smoke-test"

    comp = pd.read_csv(run_dir / "model_comparison.csv")
    assert set(comp["backend"]) == {"statsforecast", "mlforecast"}
    assert list(comp["rank"]) == list(range(1, len(comp) + 1))
    assert comp.sort_values("rank").iloc[0]["rank_metric"] == "mae"

    runtime = pd.read_csv(run_dir / "runtime_metrics.csv")
    assert {"linear", "random_forest", "naive"} <= set(runtime["model_type"])

    metrics = pd.read_csv(run_dir / "metrics.csv")
    assert set(metrics["backend"]) == {"statsforecast", "mlforecast"}

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["mlforecast"]["lags"] == [1, 24]
    assert manifest["predict"] == {"horizon": 24}
    assert set(manifest["per_backend_seed"]) == {"statsforecast", "mlforecast"}
