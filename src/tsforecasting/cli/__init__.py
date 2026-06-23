"""tsforecasting CLI entrypoint.

MVP-0 exposes three subcommands: ``validate-config``, ``run`` and ``backtest``.
``validate-config`` is wired in P2; ``run`` and ``backtest`` are wired in P6.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

_RUN_LEVEL_OVERRIDES = ("--run-id", "--output-dir", "--log-name", "--log-level")


def _add_run_overrides(parser: argparse.ArgumentParser) -> None:
    for opt in _RUN_LEVEL_OVERRIDES:
        parser.add_argument(opt, default=None)
    parser.add_argument("--dry-run", action="store_true")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tsforecasting",
        description="Unified time-series forecasting on the Nixtla stack.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate-config",
        help="Validate a YAML config without reading data or training.",
    )
    p_validate.add_argument("--config", required=True)

    p_run = sub.add_parser(
        "run",
        help="Run backtest + evaluation (and future predict if configured).",
    )
    p_run.add_argument("--config", required=True)
    _add_run_overrides(p_run)

    p_backtest = sub.add_parser(
        "backtest",
        help="Run backtest + evaluation only (no future predict).",
    )
    p_backtest.add_argument("--config", required=True)
    _add_run_overrides(p_backtest)

    p_reconcile = sub.add_parser(
        "reconcile",
        help="Hierarchical reconciliation (P9: TourismSmall).",
    )
    p_reconcile.add_argument("--config", required=True)
    _add_run_overrides(p_reconcile)

    p_report = sub.add_parser(
        "report",
        help="Generate a notebook report from a run dir (P10).",
    )
    p_report.add_argument("--run-dir", required=True)
    p_report.add_argument("--output-dir", default="reports")

    return parser


def _cmd_validate_config(args: argparse.Namespace) -> int:
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


def _load_and_resolve(args: argparse.Namespace) -> object | None:
    from tsforecasting.config import ConfigError, load_config, resolve_overrides

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return None
    resolve_overrides(
        config,
        run_id=args.run_id,
        output_dir=args.output_dir,
        log_name=args.log_name,
        log_level=args.log_level,
    )
    return config


def _print_dry_run(label: str, config: object) -> None:
    print(f"dry-run plan ({label}):")
    print(f"  run_id:      {config.run_id}")
    print(f"  output_dir:  {config.artifacts.output_dir}")
    print(f"  data:        {config.data.path}")
    print(f"  models:      {[m.name for m in config.models]}")
    print(f"  predict:     {config.predict.horizon if config.predict else 'none'}")


def _cmd_run(args: argparse.Namespace) -> int:
    from tsforecasting.orchestration import run_pipeline

    config = _load_and_resolve(args)
    if config is None:
        return 1
    if args.dry_run:
        _print_dry_run("run", config)
        return 0
    run_dir = run_pipeline(config, do_predict=True)
    print(f"run complete: {run_dir}")
    return 0


def _cmd_backtest(args: argparse.Namespace) -> int:
    from tsforecasting.orchestration import run_pipeline

    config = _load_and_resolve(args)
    if config is None:
        return 1
    if args.dry_run:
        _print_dry_run("backtest only", config)
        return 0
    run_dir = run_pipeline(config, do_predict=False)
    print(f"backtest complete: {run_dir}")
    return 0


def _load_and_resolve_hierarchical(args: argparse.Namespace) -> object | None:
    from tsforecasting.config.hierarchical import (
        ConfigError,
        load_hierarchical_config,
        resolve_hierarchical_overrides,
    )

    try:
        config = load_hierarchical_config(args.config)
    except ConfigError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return None
    resolve_hierarchical_overrides(
        config,
        run_id=args.run_id,
        output_dir=args.output_dir,
        log_name=args.log_name,
        log_level=args.log_level,
    )
    return config


def _print_dry_run_hierarchical(label: str, config: object) -> None:
    print(f"dry-run plan ({label}):")
    print(f"  run_id:      {config.run_id}")
    print(f"  output_dir:  {config.artifacts.output_dir}")
    print(f"  dataset:     {config.data.dataset}")
    print(f"  base models: {[m.name for m in config.base_forecast.models]}")
    print(f"  reconcilers: {[r.name for r in config.hierarchical.reconcilers]}")


def _cmd_reconcile(args: argparse.Namespace) -> int:
    from tsforecasting.orchestration import run_reconciliation

    config = _load_and_resolve_hierarchical(args)
    if config is None:
        return 1
    if args.dry_run:
        _print_dry_run_hierarchical("reconcile", config)
        return 0
    run_dir = run_reconciliation(config)
    print(f"reconciliation complete: {run_dir}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    try:
        from tsforecasting.reporting import generate_report

        out = generate_report(args.run_dir, output_dir=args.output_dir)
    except (ValueError, ImportError) as exc:
        print(f"report failed: {exc}", file=sys.stderr)
        return 1
    print(f"report generated: {out}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "validate-config": _cmd_validate_config,
        "run": _cmd_run,
        "backtest": _cmd_backtest,
        "reconcile": _cmd_reconcile,
        "report": _cmd_report,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
