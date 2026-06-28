"""End-to-end smoke test: the P9 TourismSmall hierarchical reconciliation path.

Artifacts are redirected to an absolute tmp ``--output-dir``. The example
config's ``data.cache_dir`` (``dataset/datasetsforecast_cache``) downloads TourismSmall
once under the repo root (gitignored). Skipped when the ``hierarchical`` extra
is not installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("hierarchicalforecast")
pytest.importorskip("datasetsforecast")

from tsforecasting.cli import main as cli_main  # noqa: E402
from tsforecasting.config.hierarchical import (  # noqa: E402
    load_hierarchical_config,
    resolve_hierarchical_overrides,
)
from tsforecasting.orchestration import run_reconciliation  # noqa: E402

EXAMPLE = Path("configs/examples/tourism_small/hierarchical.yaml")


def test_reconcile_smoke(tmp_path: Path) -> None:
    config = load_hierarchical_config(EXAMPLE)
    resolve_hierarchical_overrides(
        config, run_id="reconcile-smoke", output_dir=str(tmp_path / "results")
    )

    run_dir = run_reconciliation(config)
    assert run_dir == tmp_path / "results" / "reconcile-smoke"

    for name in [
        "base_predictions.csv",
        "reconciled_predictions.csv",
        "reconciliation_diagnostics.csv",
        "manifest.json",
        "run_config.yaml",
    ]:
        assert (run_dir / name).is_file(), name

    diag = pd.read_csv(run_dir / "reconciliation_diagnostics.csv")
    assert set(diag["reconciler"]) == {
        "bottom_up",
        "min_trace_ols",
        "top_down_forecast_proportions",
        "middle_out_state",
    }
    # all reconcilers produce coherent forecasts by construction
    assert (diag["coherent"] == True).all()  # noqa: E712
    assert np.isfinite(diag["mse"]).all()

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["run_id"] == "reconcile-smoke"
    assert "Country/Purpose/State/CityNonCity" in manifest["hierarchy_levels"]
    assert len(manifest["reconcilers"]) == 4


def test_cli_reconcile_end_to_end(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cli_main(
        [
            "reconcile",
            "--config",
            str(EXAMPLE),
            "--run-id",
            "cli-recon",
            "--output-dir",
            str(tmp_path / "results"),
        ]
    )
    assert rc == 0
    assert "reconciliation complete" in capsys.readouterr().out
    assert (tmp_path / "results" / "cli-recon").is_dir()


def test_cli_reconcile_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cli_main(
        [
            "reconcile",
            "--config",
            str(EXAMPLE),
            "--dry-run",
            "--run-id",
            "dry-recon",
            "--output-dir",
            str(tmp_path / "results"),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run plan" in out
    assert "reconcilers" in out
    assert not (tmp_path / "results").exists()
