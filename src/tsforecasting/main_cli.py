"""面向 shell 脚本的类式 CLI 入口。"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


class MainCLI:
    """tsforecasting 命令行入口。

    CLI 类只负责参数解析、配置加载和命令分发；训练、评估、报告生成分别交给
    ForecastRunner 和 reporting 类，避免命令行层混入业务流程。
    """

    def __init__(self, argv: Sequence[str] | None = None) -> None:
        self.argv = argv
        self.parser = self.build_parser()

    @staticmethod
    def add_run_overrides(parser: argparse.ArgumentParser) -> None:
        """为会产生运行目录的命令添加通用运行级覆盖参数。"""
        for opt in ("--run-id", "--output-dir", "--log-name", "--log-level"):
            parser.add_argument(opt, default=None)
        parser.add_argument("--dry-run", action="store_true")

    @classmethod
    def build_parser(cls) -> argparse.ArgumentParser:
        """构建 CLI parser；这里只声明参数，不执行业务逻辑。"""
        parser = argparse.ArgumentParser(
            prog="tsforecasting",
            description="Unified time-series forecasting on the Nixtla stack.",
        )
        sub = parser.add_subparsers(dest="command", required=True)

        p_validate = sub.add_parser(
            "validate-config",
            help="Validate a forecast YAML config without reading data or training.",
        )
        p_validate.add_argument("--config", required=True)

        p_run = sub.add_parser(
            "run",
            help="Run backtest + evaluation and forecast if configured.",
        )
        p_run.add_argument("--config", required=True)
        cls.add_run_overrides(p_run)

        p_backtest = sub.add_parser(
            "backtest",
            help="Run backtest + evaluation only.",
        )
        p_backtest.add_argument("--config", required=True)
        cls.add_run_overrides(p_backtest)

        p_report = sub.add_parser(
            "report",
            help="Generate a notebook report from a forecast run dir.",
        )
        p_report.add_argument("--run-dir", required=True)
        p_report.add_argument(
            "--html",
            action="store_true",
            help="Also execute and export HTML (nbconvert).",
        )
        return parser

    def load_and_resolve(self, args: argparse.Namespace):
        """加载 YAML 并应用 CLI override；配置错误转成友好 stderr。"""
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

    @staticmethod
    def print_dry_run(label: str, config: object) -> None:
        """打印最终生效计划，不读取数据、不训练模型、不写 artifact。"""
        print(f"dry-run plan ({label}):")
        print(f"  run_id:      {config.run_id}")
        print(f"  output_dir:  {config.output.dir}")
        print(f"  data:        {config.data.path}")
        print(f"  models:      {[m.name for m in config.models]}")
        print(f"  forecast:    {config.forecast.horizon if config.forecast else 'none'}")

    def cmd_validate(self, args: argparse.Namespace) -> int:
        """validate-config 子命令：只做 metadata-level 配置校验。"""
        from tsforecasting.config import ConfigError, load_config

        try:
            config = load_config(args.config)
        except ConfigError as exc:
            print(f"config invalid: {exc}", file=sys.stderr)
            return 1
        print("config valid")
        print(f"  data:   {config.data.path}")
        print(f"  models: {[m.name for m in config.models]}")
        print(f"  output: {config.output.dir}")
        return 0

    def cmd_run(self, args: argparse.Namespace, *, do_predict: bool) -> int:
        """run/backtest 子命令：创建 ForecastRunner 执行主流程。"""
        from tsforecasting.main import ForecastRunner

        config = self.load_and_resolve(args)
        if config is None:
            return 1
        if args.dry_run:
            self.print_dry_run("run" if do_predict else "backtest only", config)
            return 0
        run_dir = ForecastRunner(config, do_predict=do_predict).run()
        print(f"{'run' if do_predict else 'backtest'} complete: {run_dir}")
        return 0

    @staticmethod
    def cmd_report(args: argparse.Namespace) -> int:
        """report 子命令：只支持 forecast run 目录。"""
        try:
            from tsforecasting.reporting import ReportGenerator

            out = ReportGenerator(args.run_dir, html=args.html).generate()
        except Exception as exc:
            print(f"report failed: {exc}", file=sys.stderr)
            return 1
        print(f"report generated: {out}")
        if args.html:
            print(f"html report: {out.with_suffix('.html')}")
        return 0

    def run(self) -> int:
        """解析 argv 并分发到对应子命令。"""
        args = self.parser.parse_args(self.argv)
        if args.command == "validate-config":
            return self.cmd_validate(args)
        if args.command == "run":
            return self.cmd_run(args, do_predict=True)
        if args.command == "backtest":
            return self.cmd_run(args, do_predict=False)
        if args.command == "report":
            return self.cmd_report(args)
        self.parser.error(f"unknown command: {args.command}")
        return 2


def build_parser() -> argparse.ArgumentParser:
    """兼容测试/调试读取 parser 的薄函数。"""
    return MainCLI.build_parser()


def main(argv: Sequence[str] | None = None) -> int:
    """console script 入口。"""
    return MainCLI(argv).run()


if __name__ == "__main__":
    sys.exit(main())
