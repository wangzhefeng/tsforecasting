"""Tests for the vendored logging utility (lazy, idempotent, env-driven)."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from logging import handlers
from pathlib import Path

import pytest

from tsforecasting.utils import logging as tslogging


@pytest.fixture(autouse=True)
def _isolated_logger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Clean cwd, env vars, and any handlers cached on the default logger.

    Integration tests configure the shared ``tsforecasting`` logger and set
    ``LOG_NAME`` / ``SERVICE_LOG_LEVEL``; these must not leak into unit tests.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SERVICE_LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_NAME", raising=False)
    logging.getLogger(tslogging.DEFAULT_LOGGER_NAME).handlers.clear()


def test_import_is_lazy(tmp_path: Path) -> None:
    # Run in a fresh process so pytest's own log capture cannot mask the
    # lazy guarantee: importing must not attach handlers or create logs/.
    code = (
        "import json, logging, os; "
        f"os.chdir({str(tmp_path)!r}); "
        "from tsforecasting.utils import logging as L; "
        "hs = [type(h).__name__ for h in logging.getLogger(L.DEFAULT_LOGGER_NAME).handlers]; "
        "print(json.dumps({'handlers': hs, 'logs_exists': os.path.isdir('logs')}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    payload = json.loads(result.stdout)
    assert payload["handlers"] == []
    assert payload["logs_exists"] is False


def test_get_logger_attaches_console_and_file_handlers() -> None:
    logger = tslogging.get_logger("test_two_handlers")
    handler_types = {type(h).__name__ for h in logger.handlers}
    assert "StreamHandler" in handler_types
    assert "TimedRotatingFileHandler" in handler_types
    assert len(logger.handlers) == 2


def test_get_logger_is_idempotent() -> None:
    name = "test_idempotent"
    first = tslogging.get_logger(name)
    second = tslogging.get_logger(name)
    assert first is second
    assert len(second.handlers) == 2


def test_get_logger_creates_log_dir(tmp_path: Path) -> None:
    tslogging.get_logger("test_creates_dir")
    assert (tmp_path / "logs" / "main").is_dir()


def test_service_log_level_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_LOG_LEVEL", "DEBUG")
    logger = tslogging.get_logger("test_level_debug")
    assert logger.level == logging.DEBUG


def test_log_name_env_controls_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_NAME", "custom_run")
    logger = tslogging.get_logger("test_log_name")
    file_handlers = [
        h for h in logger.handlers if isinstance(h, handlers.TimedRotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    assert "custom_run" in str(Path(file_handlers[0].baseFilename))


def test_logger_does_not_propagate() -> None:
    logger = tslogging.get_logger("test_propagate")
    assert logger.propagate is False
