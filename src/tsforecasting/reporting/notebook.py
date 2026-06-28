"""普通 forecast 运行的 notebook 构建器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat as nbf

from tsforecasting.reporting.detect import load_manifest
from tsforecasting.reporting.templates import (
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
