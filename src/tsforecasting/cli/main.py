"""Main dispatcher for the tsforecasting CLI."""

from __future__ import annotations

import sys
from typing import Sequence

from tsforecasting.cli.forecast import cmd_backtest, cmd_run
from tsforecasting.cli.hierarchical import cmd_reconcile
from tsforecasting.cli.parser import build_parser
from tsforecasting.cli.report import cmd_report
from tsforecasting.cli.validate import cmd_validate_config


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "validate-config": cmd_validate_config,
        "run": cmd_run,
        "backtest": cmd_backtest,
        "reconcile": cmd_reconcile,
        "report": cmd_report,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
