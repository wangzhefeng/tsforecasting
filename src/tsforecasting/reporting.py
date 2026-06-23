"""Notebook reporting (P10).

Generates a static (un-executed) Jupyter notebook from a run's artifacts, so
the plan's "reports/{run_id}/model_comparison.ipynb can be generated from
existing artifacts" acceptance is met without pulling a Jupyter execution
stack into the base install. Two run types are detected:

* MVP-0 runs (``model_comparison.csv``) -> ``model_comparison.ipynb``
* hierarchical runs (``reconciliation_diagnostics.csv``) -> ``reconciliation.ipynb``

Code cells reference the run's CSVs by absolute path and use pandas +
matplotlib; the user runs ``Run All`` to render (needs the ``plot`` extra).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import nbformat as nbf

_PY_KERNEL = {"display_name": "Python 3", "language": "python", "name": "python3"}


def _md(text: str) -> dict[str, Any]:
    return nbf.v4.new_markdown_cell(text)


def _code(src: str) -> dict[str, Any]:
    return nbf.v4.new_code_cell(src)


def _load_manifest(run_dir: Path) -> dict[str, Any]:
    p = run_dir / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _read_run_id(run_dir: Path) -> str:
    return _load_manifest(run_dir).get("run_id") or run_dir.name


def detect_run_type(run_dir: str | Path) -> str:
    """Return ``"mvp0"`` or ``"hierarchical"`` based on which artifacts exist."""
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise ValueError(f"run_dir not found: {run_dir}")
    if (run_dir / "model_comparison.csv").exists():
        return "mvp0"
    if (run_dir / "reconciliation_diagnostics.csv").exists():
        return "hierarchical"
    raise ValueError(
        f"run_dir has neither model_comparison.csv nor "
        f"reconciliation_diagnostics.csv: {run_dir}"
    )


def _mvp0_meta_md(manifest: dict[str, Any]) -> str:
    lines: list[str] = []
    if manifest.get("config_source"):
        lines.append(f"- config: `{manifest['config_source']}`")
    if manifest.get("freq"):
        lines.append(f"- freq: `{manifest['freq']}`")
    models = manifest.get("models")
    if models:
        lines.append("- models: " + ", ".join(m.get("name", "?") for m in models))
    bt = manifest.get("backtest")
    if bt:
        lines.append(
            f"- backtest: horizon={bt.get('horizon')}, "
            f"n_windows={bt.get('n_windows')}, step_size={bt.get('step_size')}"
        )
    return "\n".join(lines)


def _hierarchical_meta_md(manifest: dict[str, Any]) -> str:
    lines: list[str] = []
    data = manifest.get("data") or {}
    if data.get("dataset"):
        lines.append(f"- dataset: `{data['dataset']}`")
    if data.get("freq"):
        lines.append(f"- freq: `{data['freq']}`")
    levels = manifest.get("hierarchy_levels")
    if levels:
        lines.append("- levels: " + ", ".join(f"{k}={v}" for k, v in levels.items()))
    bf = manifest.get("base_forecast") or {}
    if bf.get("models"):
        lines.append(
            "- base: " + ", ".join(m.get("name", "?") for m in bf["models"])
        )
    recs = manifest.get("reconcilers")
    if recs:
        lines.append("- reconcilers: " + ", ".join(r.get("name", "?") for r in recs))
    return "\n".join(lines)


_MVP0_LOAD = """import pandas as pd
run_dir = "__RUN_DIR__"
comparison = pd.read_csv(run_dir + "/model_comparison.csv")
metrics = pd.read_csv(run_dir + "/metrics.csv")
backtest = pd.read_csv(run_dir + "/backtest_predictions.csv")
runtime = pd.read_csv(run_dir + "/runtime_metrics.csv")
"""

_MVP0_RANK = "comparison.sort_values(\"rank\")"

_MVP0_METRICS = """import matplotlib.pyplot as plt
pivot = metrics.pivot_table(index="model", columns="metric", values="value")
pivot.plot.bar()
plt.ylabel("error"); plt.title("Metrics by model"); plt.tight_layout(); plt.show()
"""

_MVP0_BACKTEST = """import matplotlib.pyplot as plt
best = comparison.sort_values("rank")["model"].iloc[0]
sub = backtest[backtest["model"] == best].sort_values(["unique_id", "ds"])
for uid, g in sub.groupby("unique_id"):
    plt.figure()
    plt.plot(g["ds"], g["y"], label="actual")
    plt.plot(g["ds"], g["yhat"], label="forecast")
    plt.title(best + ": " + str(uid)); plt.legend(); plt.tight_layout(); plt.show()
"""

_MVP0_RUNTIME = """import matplotlib.pyplot as plt
runtime.set_index("model")["total_seconds"].plot.bar()
plt.ylabel("seconds"); plt.title("Runtime by model"); plt.tight_layout(); plt.show()
"""

_HIER_LOAD = """import pandas as pd
run_dir = "__RUN_DIR__"
diag = pd.read_csv(run_dir + "/reconciliation_diagnostics.csv")
base = pd.read_csv(run_dir + "/base_predictions.csv")
reconciled = pd.read_csv(run_dir + "/reconciled_predictions.csv")
"""

_HIER_LEVELS = """import json
manifest = json.load(open(run_dir + "/manifest.json"))
manifest["hierarchy_levels"]
"""

_HIER_DIAG = "diag.sort_values(\"mse\")"

_HIER_MSE = """import matplotlib.pyplot as plt
diag.set_index("reconciler")["mse"].plot.bar()
plt.ylabel("mse"); plt.title("Reconciler MSE"); plt.tight_layout(); plt.show()
"""

_HIER_RECONCILED = """import matplotlib.pyplot as plt
total = reconciled[reconciled["unique_id"] == "total"].sort_values(["reconciler", "ds"])
for rec, g in total.groupby("reconciler"):
    plt.plot(g["ds"], g["yhat"], label=rec)
base_total = base[base["unique_id"] == "total"].sort_values("ds")
plt.plot(base_total["ds"], base_total["yhat"], label="base", linestyle="--")
plt.title("Reconciled vs base (total)"); plt.legend(); plt.tight_layout(); plt.show()
"""


def build_mvp0_notebook(run_dir: str | Path, run_id: str) -> Any:
    run_dir = Path(run_dir)
    manifest = _load_manifest(run_dir)
    meta = _mvp0_meta_md(manifest)
    rd = str(run_dir)
    cells = [
        _md(
            f"# Forecast report: {run_id}\n\n{meta}\n\n"
            "> **Run All** to render tables and figures (needs `pandas` + `matplotlib`)."
        ),
        _code(_MVP0_LOAD.replace("__RUN_DIR__", rd)),
        _code(_MVP0_RANK),
        _code(_MVP0_METRICS),
        _code(_MVP0_BACKTEST),
        _code(_MVP0_RUNTIME),
    ]
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = _PY_KERNEL
    return nb


def build_hierarchical_notebook(run_dir: str | Path, run_id: str) -> Any:
    run_dir = Path(run_dir)
    manifest = _load_manifest(run_dir)
    meta = _hierarchical_meta_md(manifest)
    rd = str(run_dir)
    cells = [
        _md(
            f"# Reconciliation report: {run_id}\n\n{meta}\n\n"
            "> **Run All** to render tables and figures (needs `pandas` + `matplotlib`)."
        ),
        _code(_HIER_LOAD.replace("__RUN_DIR__", rd)),
        _code(_HIER_LEVELS),
        _code(_HIER_DIAG),
        _code(_HIER_MSE),
        _code(_HIER_RECONCILED),
    ]
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = _PY_KERNEL
    return nb


def to_html(notebook_path: str | Path) -> Path:
    """Execute the notebook and export to a self-contained HTML file (nbconvert).

    Raises on execution failure (missing data, kernel, or matplotlib); callers
    catch and degrade. Requires the ``[report]`` extra (nbconvert).
    """
    from nbconvert import HTMLExporter
    from nbconvert.preprocessors import ExecutePreprocessor

    notebook_path = Path(notebook_path)
    nb = nbf.read(str(notebook_path), as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    try:
        ep.preprocess(nb, {"metadata": {"path": str(notebook_path.parent)}})
    except Exception as exc:  # noqa: BLE001 - surface a friendly hint on missing kernel
        if type(exc).__name__ == "NoSuchKernel":
            raise ImportError(
                "no 'python3' Jupyter kernel; install it via "
                "`python -m ipykernel install --sys-prefix --name python3`"
            ) from exc
        raise
    body, _ = HTMLExporter().from_notebook_node(nb)
    html_path = notebook_path.with_suffix(".html")
    html_path.write_text(body, encoding="utf-8")
    return html_path


def generate_report(
    run_dir: str | Path,
    output_dir: str | Path = "reports",
    *,
    html: bool = False,
) -> Path:
    """Detect run type, build the matching notebook, write it under ``output_dir/run_id``.

    If ``html``, also execute the notebook and export a self-contained HTML
    report (needs the ``[report]`` extra's nbconvert; on failure the notebook
    is still written and the HTML error propagates to the caller).
    """
    run_dir = Path(run_dir).resolve()
    run_id = _read_run_id(run_dir)
    rtype = detect_run_type(run_dir)
    if rtype == "mvp0":
        nb = build_mvp0_notebook(run_dir, run_id)
        name = "model_comparison.ipynb"
    else:
        nb = build_hierarchical_notebook(run_dir, run_id)
        name = "reconciliation.ipynb"
    out_dir = Path(output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name
    nbf.write(nb, out)
    if html:
        to_html(out)
    return out
