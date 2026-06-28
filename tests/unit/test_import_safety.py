"""基础安装 import 安全回归测试。

验证未安装 ``ml``/``neural`` extra 时,主包和 stats adapter 仍可正常 import。
这是 lazy-import-optional-backend 契约的护栏:防止 ``models/nixtla/__init__.py``
顶部 import 可选 backend adapter 导致基础安装无法启动。

用独立子进程 + ``sys.modules[name] = None`` 屏蔽可选依赖,隔离 pytest 主进程
已缓存的模块,确保测到的是真实 import 链。
"""

import subprocess
import sys


def test_base_install_imports_without_optional_extras() -> None:
    """屏蔽 ml/neural extra 的子进程必须能 import 主包与 stats adapter。"""
    code = (
        "import sys; "
        "sys.modules['mlforecast'] = None; "
        "sys.modules['neuralforecast'] = None; "
        "import tsforecasting.main; "
        "from tsforecasting.models.nixtla import StatsForecastAdapter; "
        "print('ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"基础安装无法 import 主包(可选 extra 未装时应仍可用):\n{result.stderr}"
    )
