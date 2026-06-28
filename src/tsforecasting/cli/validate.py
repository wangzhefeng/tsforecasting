"""validate-config CLI 子命令实现。"""

from __future__ import annotations

import argparse
import sys


def cmd_validate_config(args: argparse.Namespace) -> int:
    """
    执行配置校验命令，并用进程返回码表达校验结果。

    Args:
        args (argparse.Namespace): argparse 解析出的命令行参数。

    Returns:
        int: 配置有效时返回 0，配置无效时返回 1。
    """
    from tsforecasting.config import ConfigError, load_config

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return 1
    
    print(f"config valid: {args.config}")
    print(f"  models: {[m.name for m in config.models]}")
    print(
        f"  metrics: {config.evaluation.metrics} "
        f"(rank by {config.evaluation.rank_metric})"
    )
    return 0
