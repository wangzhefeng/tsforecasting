"""普通 forecast 和层级协调运行的 notebook 构建器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat as nbf

from tsforecasting.reporting.detect import load_manifest
from tsforecasting.reporting.templates import (
    HIER_DIAG,
    HIER_LEVELS,
    HIER_LOAD,
    HIER_MSE,
    HIER_RECONCILED,
    MVP0_BACKTEST,
    MVP0_LOAD,
    MVP0_METRICS,
    MVP0_RANK,
    MVP0_RUNTIME,
)

_PY_KERNEL = {"display_name": "Python 3", "language": "python", "name": "python3"}


def _md(text: str) -> dict[str, Any]:
    """创建 markdown cell。"""
    return nbf.v4.new_markdown_cell(text)


def _code(src: str) -> dict[str, Any]:
    """创建 code cell。"""
    return nbf.v4.new_code_cell(src)


def _mvp0_meta_md(manifest: dict[str, Any]) -> str:
    """从普通 forecast manifest 提取报告首页摘要。"""
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
    """从层级协调 manifest 提取报告首页摘要。"""
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


def build_mvp0_notebook(run_dir: str | Path, run_id: str) -> Any:
    """构建普通 forecast 模型对比 notebook。"""
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    meta = _mvp0_meta_md(manifest)
    rd = str(run_dir)
    cells = [
        _md(
            f"# Forecast report: {run_id}\n\n{meta}\n\n"
            "> **Run All** to render tables and figures (needs `pandas` + `matplotlib`)."
        ),
        _code(MVP0_LOAD.replace("__RUN_DIR__", rd)),
        _code(MVP0_RANK),
        _code(MVP0_METRICS),
        _code(MVP0_BACKTEST),
        _code(MVP0_RUNTIME),
    ]
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = _PY_KERNEL
    return nb


def build_hierarchical_notebook(run_dir: str | Path, run_id: str) -> Any:
    """构建层级协调诊断 notebook。"""
    run_dir = Path(run_dir)
    manifest = load_manifest(run_dir)
    meta = _hierarchical_meta_md(manifest)
    rd = str(run_dir)
    cells = [
        _md(
            f"# Reconciliation report: {run_id}\n\n{meta}\n\n"
            "> **Run All** to render tables and figures (needs `pandas` + `matplotlib`)."
        ),
        _code(HIER_LOAD.replace("__RUN_DIR__", rd)),
        _code(HIER_LEVELS),
        _code(HIER_DIAG),
        _code(HIER_MSE),
        _code(HIER_RECONCILED),
    ]
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = _PY_KERNEL
    return nb
