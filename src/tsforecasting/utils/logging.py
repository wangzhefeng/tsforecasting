"""Vendored logging utility.

Behavior contract ported from the repo-top-level ``utils/log_util.py``:

- Console (stderr) handler + daily rotating file handler, same formatter.
- ``SERVICE_LOG_LEVEL`` controls the log level (default ``INFO``).
- ``LOG_NAME`` selects the subdirectory under ``logs/`` (default ``main``),
  i.e. ``logs/{LOG_NAME}/service*``.

Deliberate changes vs the original (per docs/unified-ts-framework-plan-v2.md):

- **Lazy**: handlers and the log directory are created on the first
  ``get_logger()`` call, not at import time, so importing the package has no
  filesystem side effects and tests don't create stray ``logs/`` dirs.
- **Idempotent**: ``get_logger()`` never attaches duplicate handlers.
- **CWD-relative base**: the ``logs/`` directory is resolved relative to the
  current working directory, not to this file, so the installed package does
  not depend on the repository root and never writes inside ``site-packages``.

No module inside the package may import the repo-top-level ``utils/``.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from logging import handlers
from pathlib import Path

DEFAULT_LOGGER_NAME = "tsforecasting"

_FORMATTER = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d:%(funcName)s] %(message)s"
)

_FILE_SUFFIX = "%Y-%m-%d.log"
_FILE_EXT_MATCH = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")


def _log_level() -> str:
    return os.environ.get("SERVICE_LOG_LEVEL", "INFO")


def _log_dir() -> Path:
    return Path("logs") / os.environ.get("LOG_NAME", "main")


def get_logger(name: str = DEFAULT_LOGGER_NAME) -> logging.Logger:
    """Return the named logger, lazily attaching console + rotating file handlers.

    Calling this repeatedly with the same ``name`` returns the same logger
    without stacking additional handlers.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = _log_level()
    logger.setLevel(level)
    logger.propagate = False

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(_FORMATTER)
    logger.addHandler(stream_handler)

    log_dir = _log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = handlers.TimedRotatingFileHandler(
        filename=log_dir / "service",
        when="MIDNIGHT",
        interval=1,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.suffix = _FILE_SUFFIX
    file_handler.extMatch = _FILE_EXT_MATCH
    file_handler.setLevel(level)
    file_handler.setFormatter(_FORMATTER)
    logger.addHandler(file_handler)

    return logger
