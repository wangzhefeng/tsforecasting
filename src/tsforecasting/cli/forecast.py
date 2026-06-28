"""普通 forecast/backtest CLI 子命令实现。"""

from __future__ import annotations

import argparse
import sys


def load_and_resolve(args: argparse.Namespace) -> object | None:
    """加载配置、应用 CLI override；配置错误转成 CLI 友好返回。"""
    from tsforecasting.config import ConfigError, load_config, resolve_overrides

    try:
        config = load_config(args.config)
        resolve_overrides(
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


def print_dry_run(label: str, config: object) -> None:
    """打印最终生效的运行计划；不读取数据、不训练模型、不写 artifact。"""
    print(f"dry-run plan ({label}):")
    print(f"  run_id:      {config.run_id}")
    print(f"  output_dir:  {config.artifacts.output_dir}")
    print(f"  data:        {config.data.path}")
    print(f"  models:      {[m.name for m in config.models]}")
    print(f"  predict:     {config.predict.horizon if config.predict else 'none'}")


def cmd_run(args: argparse.Namespace) -> int:
    from tsforecasting.orchestration import run_pipeline

    # 加载配置并应用运行级覆盖；非法配置在这里转为友好的 CLI 错误。
    config = load_and_resolve(args)
    # 配置解析失败时停止执行，避免进入数据读取或模型训练。
    if config is None:
        return 1
    # dry-run 只展示最终生效的运行计划，不产生 artifact。
    if args.dry_run:
        print_dry_run("run", config)
        return 0
    # run 命令包含未来预测，因此 do_predict=True。
    run_dir = run_pipeline(config, do_predict=True)
    print(f"run complete: {run_dir}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    """执行只回测不未来预测的 CLI 命令。"""
    from tsforecasting.orchestration import run_pipeline

    config = load_and_resolve(args)
    if config is None:
        return 1
    if args.dry_run:
        print_dry_run("backtest only", config)
        return 0
    run_dir = run_pipeline(config, do_predict=False)
    print(f"backtest complete: {run_dir}")
    return 0
