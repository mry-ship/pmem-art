"""本机 pmem_art CLI 启动器：Windows=pyw，macOS/Linux=python3。

技能源码里可继续写 ``python3 pmem_art.py``（跨仓可读）；
安装到本机、以及运行时打印给 Agent 的命令，一律经本模块改成当前平台前缀。

独立于 skills_kit，避免 lifecycle ↔ skills_kit 循环导入。
"""
from __future__ import annotations

import re
import sys


def cli_python_prefix(*, platform: str | None = None) -> str:
    """返回解释器前缀（不含 pmem_art.py）。"""
    plat = platform if platform is not None else sys.platform
    if plat == "win32":
        return "pyw -3 -u"
    return "python3"


def pmem_art_cli(*, platform: str | None = None) -> str:
    """返回本机应照抄的完整入口，如 ``pyw -3 -u pmem_art.py``。"""
    return f"{cli_python_prefix(platform=platform)} pmem_art.py"


_LAUNCHER_RE = re.compile(
    r"(?:python3|pythonw|python|pyw\s+-3\s+-u|py\s+-3\s+-u|py\s+-3)\s+pmem_art\.py"
)


def rewrite_cli_invocations(text: str, *, platform: str | None = None) -> str:
    """把文中所有 pmem_art.py 启动器统一成当前平台写法。"""
    if not text:
        return text
    target = pmem_art_cli(platform=platform)
    return _LAUNCHER_RE.sub(target, text)


# Shell 里常见的控制台解释器：python / python3 / py -3（不含路径里的 python.exe）
_SHELL_CONSOLE_PY = re.compile(
    r"(?i)(^|[^\\/\w])(?:python3|python)(?=\s)"
)
_SHELL_CONSOLE_PY_LAUNCHER = re.compile(
    r"(?i)(^|[^\\/\w])py\s+-3(?!\s+-u)(?=\s)"
)


def rewrite_shell_to_windowless(
    command: str, *, platform: str | None = None
) -> str | None:
    """Windows：把 Shell 命令里的控制台 python 改成 pyw，避免每条命令弹黑框。

    返回改写后的命令；无需改动时返回 None。
    """
    if (platform if platform is not None else sys.platform) != "win32":
        return None
    original = str(command or "")
    if not original.strip():
        return None
    out = _SHELL_CONSOLE_PY.sub(r"\1pyw -3 -u", original)
    out = _SHELL_CONSOLE_PY_LAUNCHER.sub(r"\1pyw -3 -u", out)
    out = re.sub(r"(?:pyw\s+-3\s+-u\s+)+", "pyw -3 -u ", out)
    if out == original:
        return None
    return out
