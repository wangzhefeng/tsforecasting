"""notebook 执行与 HTML 导出 helper。"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf


def to_html(notebook_path: str | Path) -> Path:
    """执行 notebook 并导出单文件 HTML。"""
    from nbconvert import HTMLExporter
    from nbconvert.preprocessors import ExecutePreprocessor

    notebook_path = Path(notebook_path)
    nb = nbf.read(str(notebook_path), as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    try:
        ep.preprocess(nb, {"metadata": {"path": str(notebook_path.parent)}})
    except Exception as exc:  # noqa: BLE001 - 为缺失 kernel 提供更友好的错误提示。
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
