"""Tests for the P10 reporting module (notebook generation).

Synthesizes tiny MVP-0 and hierarchical run dirs so notebook structure is
verified without executing any model. Skipped when the ``report`` extra
(``nbformat``) is not installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("nbformat")

from tsforecasting.reporting import (  # noqa: E402
    build_hierarchical_notebook,
    build_mvp0_notebook,
    detect_run_type,
    generate_report,
)


def _mvp0_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "runs" / "mvp0-run"
    run_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"run_id": "mvp0-run", "backend": "statsforecast", "model": "auto_ets", "model_type": "ets", "mae": 1.0, "rmse": 1.2, "mape": 0.1, "smape": 0.08, "total_seconds": 0.5, "rank_metric": "mae", "rank": 1},
            {"run_id": "mvp0-run", "backend": "statsforecast", "model": "seasonal_naive", "model_type": "naive", "mae": 1.4, "rmse": 1.6, "mape": 0.15, "smape": 0.1, "total_seconds": 0.4, "rank_metric": "mae", "rank": 2},
        ]
    ).to_csv(run_dir / "model_comparison.csv", index=False)
    json.dump(
        {
            "run_id": "mvp0-run",
            "config_source": "ett_small_stats.yaml",
            "freq": "1h",
            "models": [{"name": "auto_ets", "backend": "statsforecast", "params": {}}],
            "backtest": {"horizon": 24, "n_windows": 3, "step_size": 24},
        },
        open(run_dir / "manifest.json", "w"),
    )
    return run_dir


def _hier_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "runs" / "hier-run"
    run_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"run_id": "hier-run", "base_model": "seasonal_naive", "reconciler": "min_trace_ols", "coherent": True, "mse": 100.0},
            {"run_id": "hier-run", "base_model": "seasonal_naive", "reconciler": "bottom_up", "coherent": True, "mse": 120.0},
        ]
    ).to_csv(run_dir / "reconciliation_diagnostics.csv", index=False)
    json.dump(
        {
            "run_id": "hier-run",
            "data": {"dataset": "TourismSmall", "freq": "QE"},
            "hierarchy_levels": {"Country": 1, "Country/Purpose/State/CityNonCity": 56},
            "base_forecast": {"backend": "statsforecast", "horizon": 4, "models": [{"name": "seasonal_naive"}]},
            "reconcilers": [{"name": "min_trace_ols"}],
        },
        open(run_dir / "manifest.json", "w"),
    )
    return run_dir


def test_detect_mvp0(tmp_path: Path) -> None:
    assert detect_run_type(_mvp0_run(tmp_path)) == "mvp0"


def test_detect_hierarchical(tmp_path: Path) -> None:
    assert detect_run_type(_hier_run(tmp_path)) == "hierarchical"


def test_detect_unknown_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="run_dir"):
        detect_run_type(empty)


def test_mvp0_notebook_is_static_and_references_artifacts(tmp_path: Path) -> None:
    nb = build_mvp0_notebook(_mvp0_run(tmp_path), run_id="mvp0-run")
    src = "\n".join(c["source"] for c in nb["cells"])
    assert "model_comparison" in src
    assert "mvp0-run" in src  # run id surfaced in metadata
    # static: code cells carry no outputs
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == []
            assert cell["execution_count"] is None


def test_hierarchical_notebook_references_diagnostics(tmp_path: Path) -> None:
    nb = build_hierarchical_notebook(_hier_run(tmp_path), run_id="hier-run")
    src = "\n".join(c["source"] for c in nb["cells"])
    assert "reconciliation_diagnostics" in src
    assert "hier-run" in src
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == []


def test_generate_report_writes_readable_notebook(tmp_path: Path) -> None:
    import nbformat

    run_dir = _mvp0_run(tmp_path)
    out = generate_report(run_dir, output_dir=tmp_path / "reports")
    assert out.name == "model_comparison.ipynb"
    assert out.parent.parent == tmp_path / "reports"
    # round-trips through nbformat
    nbformat.read(out, as_version=4)

    hier_out = generate_report(_hier_run(tmp_path), output_dir=tmp_path / "reports")
    assert hier_out.name == "reconciliation.ipynb"


def test_to_html_executes_and_exports(tmp_path: Path) -> None:
    pytest.importorskip("nbconvert")
    import nbformat

    from tsforecasting.reporting import to_html

    nb = nbformat.v4.new_notebook()
    nb["cells"] = [nbformat.v4.new_code_cell("print(2 + 2)")]
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    p = tmp_path / "t.ipynb"
    nbformat.write(nb, p)
    html = to_html(p)
    assert html.suffix == ".html"
    assert "4" in html.read_text()  # executed print output
