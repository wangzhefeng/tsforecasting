"""配置驱动的 reconciler 解析。"""

from __future__ import annotations

from typing import Any

from tsforecasting.config.hierarchical import ReconcilerSpec
from tsforecasting.utils.imports import instantiate_from_spec


def resolve_reconciler(spec: ReconcilerSpec) -> Any:
    """根据 ``{class_path, params}`` spec 实例化 reconciler。"""
    return instantiate_from_spec(spec.class_path, spec.params)
