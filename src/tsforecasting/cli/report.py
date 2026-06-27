"""Report generation CLI command."""

from __future__ import annotations

import argparse
import sys


def cmd_report(args: argparse.Namespace) -> int:
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
