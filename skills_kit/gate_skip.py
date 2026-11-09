"""生产纪律：跳过 route / reasonableness 闸门须显式授权 + 原因。

允许条件（同时满足）：
1. CLI 传了 skip 标志（或兼容旧 env PMEM_ART_SKIP_*）
2. 提供非空 --skip-reason
3. 环境白名单：PMEM_ART_ALLOW_GATE_SKIP=1，或检测到 pytest（PYTEST_CURRENT_TEST）

仅设 PMEM_ART_SKIP_ROUTE_GATE=1 而不开 ALLOW / 不写 reason → 拒绝。
"""
from __future__ import annotations

import os
from typing import Any


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def gate_skip_context_ok() -> bool:
    """调试/单测白名单是否打开。"""
    if _truthy("PMEM_ART_ALLOW_GATE_SKIP"):
        return True
    if os.environ.get("PYTEST_CURRENT_TEST", "").strip():
        return True
    # unittest 常用
    if os.environ.get("PMEM_ART_UNDER_TEST", "").strip().lower() in ("1", "true", "yes"):
        return True
    return False


def resolve_skip_request(
    *,
    flag: bool,
    reason: str = "",
    env_name: str = "PMEM_ART_SKIP_ROUTE_GATE",
) -> tuple[bool, str]:
    """返回 (allowed_to_skip, message)。

    - flag/env 都未请求跳过 → (False, "") 表示「不要跳，走正常闸」
    - 请求了但未授权/无 reason → 抛出用的错误信息，调用方应 return 1
    - 授权成功 → (True, audit_line)
    """
    env_skip = _truthy(env_name)
    want = bool(flag) or env_skip
    if not want:
        return False, ""
    why = (reason or "").strip()
    under_test = gate_skip_context_ok()
    if not why and under_test:
        why = "test"
    if not why:
        return False, (
            f"拒绝跳过闸门：请加 --skip-reason \"…\"，并设置 PMEM_ART_ALLOW_GATE_SKIP=1"
            f"（或仅在 pytest 内）。禁止裸用 --skip / {env_name}。"
        )
    if not under_test:
        return False, (
            f"拒绝跳过闸门：未授权调试环境。设置 PMEM_ART_ALLOW_GATE_SKIP=1 后重试"
            f"（reason={why!r}）。日常请先 route / reasonableness，或 converge start --route-id 点名种闸。"
        )
    src = "flag" if flag else f"env:{env_name}"
    return True, f"gate_skip ok source={src} reason={why}"


def audit_skip_event(kind: str, message: str) -> dict[str, Any]:
    return {"kind": kind, "message": message, "allow_env": gate_skip_context_ok()}
