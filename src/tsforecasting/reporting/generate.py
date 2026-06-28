"""报告生成的高层入口。"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

from tsforecasting.reporting.detect import detect_run_type, read_run_id
from tsforecasting.reporting.export import to_html
from tsforecasting.reporting.notebook import build_mvp0_notebook


class ReportGenerator:
    """forecast run 目录报告生成器。"""

    def __init__(
        self,
        run_dir: str | Path,
        output_dir: str | Path | None = None,
        *,
        html: bool = False,
    ) -> None:
        self.run_dir = Path(run_dir).resolve()
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.html = html

    def generate(self) -> Path:
        """识别 forecast run，生成 notebook，并按需执行导出 HTML。"""
        run_id = read_run_id(self.run_dir)
        rtype = detect_run_type(self.run_dir)
        if rtype != "forecast":
            raise ValueError(f"unsupported report run type: {rtype}")
        nb = build_mvp0_notebook(self.run_dir, run_id)
        out_dir = self.output_dir if self.output_dir is not None else self.run_dir / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "model_comparison.ipynb"
        nbf.write(nb, out)
        if self.html:
            to_html(out)
        return out


def generate_report(
    run_dir: str | Path,
    output_dir: str | Path | None = None,
    *,
    html: bool = False,
) -> Path:
    """函数式兼容入口；内部委托 ReportGenerator。"""
    return ReportGenerator(run_dir, output_dir, html=html).generate()
