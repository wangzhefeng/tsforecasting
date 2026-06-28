"""小型 JSON/YAML 持久化 helper。"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import yaml


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """写入 UTF-8 JSON，自动创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_yaml(path: Path, payload: Any) -> None:
    """写入 UTF-8 YAML，保持字段顺序便于人工审阅。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def dataclass_to_yaml(path: Path, config: Any) -> None:
    """把 dataclass 配置对象转换成普通 dict 后写入 YAML。"""
    write_yaml(path, dataclasses.asdict(config))
