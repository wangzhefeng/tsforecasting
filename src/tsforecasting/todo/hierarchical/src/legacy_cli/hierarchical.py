"""层级协调 reconcile CLI 子命令实现。"""

from __future__ import annotations

import argparse
import sys


def load_and_resolve_hierarchical(args: argparse.Namespace) -> object | None:
    """加载层级配置、应用 CLI override；配置错误转成 CLI 友好返回。"""
    from tsforecasting.config.hierarchical import (
        ConfigError,
        load_hierarchical_config,
        resolve_hierarchical_overrides,
    )

    try:
        config = load_hierarchical_config(args.config)
        resolve_hierarchical_overrides(
            config,
            run_id=args.run_id,
            output_dir=args.output_dir,
            log_name=args.log_name,
            log_level=args.log_level,
        )
    except ConfigError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return None
    return config


def print_dry_run_hierarchical(label: str, config: object) -> None:
    """打印层级协调 dry-run 计划；不加载数据、不执行 reconcile。"""
    print(f"dry-run plan ({label}):")
    print(f"  run_id:      {config.run_id}")
    print(f"  output_dir:  {config.artifacts.output_dir}")
    print(f"  dataset:     {config.data.dataset}")
    print(f"  base models: {[m.name for m in config.base_forecast.models]}")
    print(f"  reconcilers: {[r.name for r in config.hierarchical.reconcilers]}")


def cmd_reconcile(args: argparse.Namespace) -> int:
    """执行层级协调 CLI 命令。"""
    from tsforecasting.orchestration import run_reconciliation

    config = load_and_resolve_hierarchical(args)
    if config is None:
        return 1
    if args.dry_run:
        print_dry_run_hierarchical("reconcile", config)
        return 0
    run_dir = run_reconciliation(config)
    print(f"reconciliation complete: {run_dir}")
    return 0
