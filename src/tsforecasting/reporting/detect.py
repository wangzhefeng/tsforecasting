"""报告生成使用的运行目录识别和 manifest 读取 helper。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_manifest(run_dir: Path) -> dict[str, Any]:
    """读取 manifest.json；缺失时返回空 dict，允许报告使用目录名兜底。"""
    p = run_dir / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def read_run_id(run_dir: Path) -> str:
    """优先从 manifest 读取 run_id；缺失时用运行目录名。"""
    return load_manifest(run_dir).get("run_id") or run_dir.name


def detect_run_type(run_dir: str | Path) -> str:
    """根据 artifact 文件判断运行类型：普通 forecast 或层级协调。"""
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
