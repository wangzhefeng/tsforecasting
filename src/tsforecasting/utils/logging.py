"""项目内置日志工具。

行为契约来自原仓库顶层 ``utils/log_util.py``：

- 同时写 stderr 和按天滚动的文件日志，格式保持一致。
- ``SERVICE_LOG_LEVEL`` 控制日志级别，默认 ``INFO``。
- ``LOG_NAME`` 控制 ``logs/`` 下的子目录，默认 ``main``，
  即 ``logs/{LOG_NAME}/service*``。

相对原实现的刻意调整：

- 延迟初始化：首次 ``get_logger()`` 时才创建 handler 和日志目录，import 包不产生文件系统副作用。
- 幂等：重复调用 ``get_logger()`` 不会重复挂 handler。
- 相对当前工作目录写日志：安装后的包不会依赖仓库根目录，也不会写入 ``site-packages``。

包内模块不能导入仓库顶层 ``utils/``。
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
    """返回指定 logger，并延迟挂载控制台和按天滚动的文件 handler。

    同名 logger 重复调用会复用已有 handler，避免日志重复输出。
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
