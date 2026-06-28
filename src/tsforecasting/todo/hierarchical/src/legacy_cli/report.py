"""report CLI 子命令实现。"""

from __future__ import annotations

import argparse
import sys


def cmd_report(args: argparse.Namespace) -> int:
    """从已有运行目录生成报告；业务逻辑延迟导入 reporting 包。"""
    try:
        from tsforecasting.reporting import generate_report

        out = generate_report(
            args.run_dir, output_dir=args.output_dir, html=args.html
        )
    except (ValueError, ImportError) as exc:
        print(f"report failed: {exc}", file=sys.stderr)
        return 1
    print(f"report generated: {out}")
    if args.html:
        print(f"html report: {out.with_suffix('.html')}")
    return 0
