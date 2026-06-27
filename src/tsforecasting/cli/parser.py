"""Argument parser construction for the tsforecasting CLI."""

from __future__ import annotations

import argparse

_RUN_LEVEL_OVERRIDES = ("--run-id", "--output-dir", "--log-name", "--log-level")


def _add_run_overrides(parser: argparse.ArgumentParser) -> None:
    """
    为会产生运行目录的命令添加通用运行级覆盖参数。

    Args:
        parser (argparse.ArgumentParser): 需要追加参数的子命令解析器。
    """
    for opt in _RUN_LEVEL_OVERRIDES:
        parser.add_argument(opt, default=None)
    parser.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tsforecasting",
        description="Unified time-series forecasting on the Nixtla stack.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # 仅校验 YAML 配置结构和模型注册信息，不读取数据或训练模型。
    p_validate = sub.add_parser(
        "validate-config",
        help="Validate a YAML config without reading data or training.",
    )
    p_validate.add_argument("--config", required=True)
    # 完整预测流程：回测、评估，并在配置 predict 时输出未来预测。
    p_run = sub.add_parser(
        "run",
        help="Run backtest + evaluation (and future predict if configured).",
    )
    p_run.add_argument("--config", required=True)
    _add_run_overrides(p_run)
    # 只执行历史回测和评估，不生成未来预测。
    p_backtest = sub.add_parser(
        "backtest",
        help="Run backtest + evaluation only (no future predict).",
    )
    p_backtest.add_argument("--config", required=True)
    _add_run_overrides(p_backtest)
    # 独立的层级预测协调流程，使用 HierarchicalConfig。
    p_reconcile = sub.add_parser(
        "reconcile",
        help="Hierarchical reconciliation (P9: TourismSmall).",
    )
    p_reconcile.add_argument("--config", required=True)
    _add_run_overrides(p_reconcile)
    # 从已有运行目录生成 notebook 报告，可选执行并导出 HTML。
    p_report = sub.add_parser(
        "report",
        help="Generate a notebook report from a run dir (P10).",
    )
    p_report.add_argument("--run-dir", required=True)
    p_report.add_argument("--output-dir", default="reports")
    p_report.add_argument(
        "--html",
        action="store_true",
        help="Also execute and export HTML (nbconvert).",
    )

    return parser
