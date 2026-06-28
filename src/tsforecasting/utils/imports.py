"""配置驱动的动态 import 和实例化 helper。"""

from __future__ import annotations

import importlib
from typing import Any


def resolve_class(class_path: str) -> type:
    """解析 ``pkg.module.Class`` 字符串并返回类对象。"""
    module_path, _, cls_name = class_path.rpartition(".")
    if not module_path or not cls_name:
        raise ValueError(f"invalid class path '{class_path}'")
    return getattr(importlib.import_module(module_path), cls_name)


def instantiate_from_spec(class_path: str, params: dict[str, Any] | None = None) -> Any:
    """按类路径和 kwargs 实例化对象。"""
    return resolve_class(class_path)(**(params or {}))


def instantiate_serialized_spec(spec: dict[str, Any]) -> Any:
    """按 ``{class, args?, kwargs?}`` spec 实例化对象。"""
    class_path = spec["class"]
    cls = resolve_class(class_path)
    return cls(*spec.get("args") or [], **(spec.get("kwargs") or {}))
