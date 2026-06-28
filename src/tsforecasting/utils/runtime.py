"""workflow 共享的运行环境初始化。"""

from __future__ import annotations

import os

import numpy as np

from tsforecasting.utils.logging import get_logger


def configure_run_environment(log_name: str, log_level: str, seed: int):
    """设置日志环境变量和 numpy 随机种子，并返回项目 logger。"""
    os.environ["LOG_NAME"] = log_name
    os.environ["SERVICE_LOG_LEVEL"] = log_level
    np.random.seed(seed)
    return get_logger()
