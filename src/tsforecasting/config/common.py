"""配置模块共享的基础能力：公共类型、YAML 读取、run_id 与运行级覆盖。"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

import yaml

VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigError(ValueError):
    """
    配置文件不满足 schema 或跨字段约束时抛出。
    """


@dataclass
class RuntimeConfig:
    collect_timing: bool = True
    log_name: str = "main"
    log_level: str = "INFO"


@dataclass
class ArtifactsConfig:
    output_dir: str
    save_plots: bool = False


def require(mapping: dict, key: str, ctx: str) -> Any:
    """
    从 mapping 中读取必填 key；缺失时带上配置上下文报错。
    """
    if key not in mapping:
        raise ConfigError(f"{ctx}: missing required key '{key}'")
    return mapping[key]


def require_str(mapping: dict, key: str, ctx: str) -> str:
    """
    读取必填字符串字段，并拒绝空字符串，避免路径、模型名等字段静默为空。
    """
    val = require(mapping, key, ctx)
    if not isinstance(val, str) or not val.strip():
        raise ConfigError(f"{ctx}: '{key}' must be a non-empty string")
    return val


def require_pos_int(mapping: dict, key: str, ctx: str) -> int:
    """
    读取必填正整数字段；bool 是 int 子类，需显式排除。
    """
    val = require(mapping, key, ctx)
    if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
        raise ConfigError(f"{ctx}: '{key}' must be a positive integer")
    return val


def build_runtime(raw: dict) -> RuntimeConfig:
    """
    构造运行配置；未显式配置时使用 CLI/workflow 的默认日志行为。
    """
    return RuntimeConfig(
        collect_timing=bool(raw.get("collect_timing", True)),
        log_name=raw.get("log_name", "main"),
        log_level=raw.get("log_level", "INFO"),
    )


def build_artifacts(raw: dict) -> ArtifactsConfig:
    """
    构造 artifact 配置，并确保 output_dir 是有效字符串。
    """
    return ArtifactsConfig(
        output_dir=require_str(raw, "output_dir", "artifacts"),
        save_plots=bool(raw.get("save_plots", False)),
    )


def load_yaml_mapping(path: str | Path) -> tuple[Path, dict]:
    """
    读取 YAML，并要求根节点是 mapping，便于后续按 section 构建 dataclass。
    """
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {path}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")
    return p, raw


def generate_run_id() -> str:
    """
    生成默认 run_id：UTC 时间戳保证可排序，随机后缀避免同秒碰撞。
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"tsforecasting-{ts}-{secrets.token_hex(4)}"


TConfig = TypeVar("TConfig")


def apply_run_overrides(
    config: TConfig,
    *,
    run_id: str | None = None,
    output_dir: str | None = None,
    log_name: str | None = None,
    log_level: str | None = None,
    validate: Callable[[TConfig], TConfig],
) -> TConfig:
    """
    原地应用 CLI 运行级覆盖，补齐默认 run_id，并重新执行配置校验。
    """
    if run_id is not None:
        config.run_id = run_id
    elif config.run_id is None:
        config.run_id = generate_run_id()
    if output_dir is not None:
        config.artifacts.output_dir = output_dir
    if log_name is not None:
        config.runtime.log_name = log_name
    if log_level is not None:
        config.runtime.log_level = log_level.upper()
    return validate(config)
