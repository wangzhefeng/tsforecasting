"""报告生成的高层入口。"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

from tsforecasting.reporting.detect import detect_run_type, read_run_id
from tsforecasting.reporting.export import to_html
from tsforecasting.reporting.notebook import (
    build_hierarchical_notebook,
    build_mvp0_notebook,
)


def generate_report(
    run_dir: str | Path,
    output_dir: str | Path = "reports",
    *,
    html: bool = False,
) -> Path:
    """识别运行类型，生成对应 notebook，并按需执行导出 HTML。"""
    run_dir = Path(run_dir).resolve()
    run_id = read_run_id(run_dir)
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
