#!/usr/bin/env python3
"""
pmem-art feedback: 把画师在 Cursor 对话里说的自然语言反馈，自动沉淀为美术记忆。

核心心智模型（个人积累记忆，不是审稿台）：
  生图 → 你说「哪里不对 / 这版留着 / 换成水彩」 → 记忆长大 → 下次生图更准。

画师不需要手写 YAML；Agent 或你自己只要把原话丢给：
  python3 pmem_art.py feedback "太赛博了，别这样画" --module character.Astra --asset assets/...
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

KIND_META = {
    "style_redline": "风格红线",
    "visual_correction": "视觉勘误",
    "art_decision": "审美拍板",
    "recipe": "定稿配方",
    "asset_record": "资产台账",
    "pipeline_constraint": "管线规格",
    "art_plan": "待产计划",
}

# 自然语言触发词 → 记忆类型（中文优先，面向画师）
# 顺序重要：先匹配「留着/定稿」再匹配「别/不要」
KEEP_PATTERNS = [
    r"这版留着", r"留着这版", r"就这个", r"就用这张", r"定稿", r"过了", r"通过",
    r"可以用", r"保留", r"keep\s*(this|it)", r"ship\s*it", r"lgtm", r"approved",
]
REJECT_PATTERNS = [
    r"别这样画", r"不要这样", r"别再", r"不要再", r"禁止", r"严禁",
    r"太赛博", r"太霓虹", r"太Q版", r"头太大", r"头身不对", r"比例不对",
    r"发色不对", r"颜色不对", r"太粉", r"太紫", r"漏抠", r"黑底",
    r"don't", r"do not", r"never\s+draw", r"reject", r"wrong",
]
FIX_PATTERNS = [
    r"改成", r"换成", r"调整", r"修一下", r"改一下", r"改成水彩", r"换成水彩",
    r"换成Q版", r"改成Q版", r"换成像素", r"改成像素", r"换成厚涂",
    r"change\s+to", r"make\s+it", r"switch\s+to",
]
DECISION_PATTERNS = [
    r"就定", r"拍板", r"以后都", r"统一用", r"风格定", r"色板定",
    r"decide", r"from\s+now", r"baseline",
]


def _now_cst() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


def _sha16(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def detect_kind(text: str) -> str:
    t = text.strip()
    low = t.lower()
    for pat in KEEP_PATTERNS:
        if re.search(pat, t, re.I) or re.search(pat, low, re.I):
            return "recipe"  # keep → 定稿配方 / 正向锚点；同时可挂 asset_record
    for pat in REJECT_PATTERNS:
        if re.search(pat, t, re.I) or re.search(pat, low, re.I):
            return "style_redline"
    for pat in DECISION_PATTERNS:
        if re.search(pat, t, re.I) or re.search(pat, low, re.I):
            return "art_decision"
    for pat in FIX_PATTERNS:
        if re.search(pat, t, re.I) or re.search(pat, low, re.I):
            return "visual_correction"
    # 默认：当作视觉勘误（具体反馈）
    return "visual_correction"


def detect_style_fork(text: str) -> str | None:
    mapping = [
        (r"水彩|watercolor", "Watercolor"),
        (r"Q版|q版|chibi|二头身|三头身", "Chibi"),
        (r"像素|pixel", "Pixel"),
        (r"赛博|cyber|霓虹|neon", "Cyber"),
        (r"厚涂|oil\s*paint", "Painterly"),
        (r"线稿|lineart|线稿图", "Lineart"),
        (r"扁平|flat", "Flat"),
    ]
    for pat, name in mapping:
        if re.search(pat, text, re.I):
            return name
    return None


def infer_module_from_text(text: str, data: dict[str, Any]) -> str:
    """从反馈文本里猜模块：命中已有模块名 / 实体名 / 领域词。"""
    modules = data.get("modules") or {}
    # 1) 显式模块 id
    for mid in modules:
        if mid in text or mid.split(".")[-1] in text:
            return mid
    # 2) 中文实体别名（从 summary / aliases 粗扫）
    for e in data.get("entries") or []:
        aliases = e.get("aliases") or []
        for a in aliases:
            if isinstance(a, str) and a and a in text:
                return e.get("module") or "brand.WorldStyle"
        summary = e.get("summary") or ""
        # skip
    # 3) 领域词
    domain_map = [
        (r"UI|界面|弹窗|图标|九宫格|按钮", "ui"),
        (r"特效|刀光|VFX|序列帧|粒子", "vfx"),
        (r"场景|气氛|背景|ruins|场景图", "scene"),
        (r"动画|Spine|Live2D|骨骼", "anim"),
        (r"角色|立绘|人物|表情|头身", "character"),
        (r"色板|风格|世界观|brand", "brand"),
    ]
    cat = None
    for pat, c in domain_map:
        if re.search(pat, text, re.I):
            cat = c
            break
    if cat:
        # 找该领域第一个 active 模块
        for mid, cfg in modules.items():
            if mid.startswith(cat + ".") and (cfg or {}).get("status", "active") == "active":
                return mid
        return f"{cat}.General"
    # 4) fallback
    for mid in ("brand.WorldStyle", "brand.GlobalStyle"):
        if mid in modules:
            return mid
    if modules:
        return next(iter(modules))
    return "brand.WorldStyle"


def _next_id(entries_dir: Path, kind: str) -> str:
    import time
    stamp = _now_cst().strftime("%Y%m%d%H%M%S")
    ms = int(time.time() * 1000) % 1000
    short = {
        "style_redline": "REDLINE",
        "visual_correction": "FIX",
        "art_decision": "DECISION",
        "recipe": "RECIPE",
        "asset_record": "ASSET",
        "pipeline_constraint": "PIPE",
        "art_plan": "PLAN",
    }.get(kind, "NOTE")
    base = f"CHAT{stamp}{ms:03d}{short}"
    # ensure unique under module dir
    n = 0
    candidate = base
    while (entries_dir / f"{candidate}.md").exists():
        n += 1
        candidate = f"{base}{n}"
    return candidate


def write_memory_entry(
    root: Path,
    *,
    module: str,
    kind: str,
    summary: str,
    body: str,
    asset: str = "",
    role: str = "reference",
    caption: str = "",
    aliases: list[str] | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> Path:
    proj_id = ""
    proj_name = ""
    try:
        from improve import ensure_project_library_bound, slugify_project_id
        meta = ensure_project_library_bound(root)
        proj_id = meta.get("project_id") or slugify_project_id(root.name)
        proj_name = meta.get("project_name") or root.name
    except Exception:
        proj_id = root.name.lower()
        proj_name = root.name
    entries_root = root / ".memory-art" / "entries" / module
    entries_root.mkdir(parents=True, exist_ok=True)
    eid = _next_id(entries_root, kind)
    now = _now_cst().strftime("%Y-%m-%d")
    assets_block = ""
    if asset:
        rel = asset
        p = root / asset
        if not p.is_file() and Path(asset).is_file():
            # allow absolute
            try:
                rel = str(Path(asset).resolve().relative_to(root))
                p = root / rel
            except Exception:
                p = Path(asset)
        sha = _sha16(p) if p.is_file() else ""
        if caption:
            cap = caption.strip()
        elif role == "approved":
            cap = f"✅ 正例定稿：{summary}"
        elif role == "rejected":
            cap = f"❌ 反例警示：{summary}"
        else:
            cap = f"📌 参考说明：{summary}"
        assets_block = (
            f"assets:\n"
            f"  - path: {rel}\n"
            f"    role: {role}\n"
            f"    caption: {json.dumps(cap, ensure_ascii=False)}\n"
        )
        if sha:
            assets_block += f"    sha256_16: {sha}\n"

    alias_line = ""
    if aliases:
        alias_line = "aliases: [" + ", ".join(json.dumps(a, ensure_ascii=False) for a in aliases) + "]\n"

    extra = ""
    if extra_meta:
        for k, v in extra_meta.items():
            if isinstance(v, (dict, list)):
                extra += f"{k}: {json.dumps(v, ensure_ascii=False)}\n"
            else:
                extra += f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, str) else v}\n"

    content = (
        f"---\n"
        f"id: {eid}\n"
        f"project_id: {json.dumps(proj_id, ensure_ascii=False)}\n"
        f"project_name: {json.dumps(proj_name, ensure_ascii=False)}\n"
        f"layer_scope: private\n"
        f"module: {module}\n"
        f"kind: {kind}\n"
        f"status: active\n"
        f"note_date: '{now}'\n"
        f"verified: '{now}'\n"
        f"author: Cursor对话·画师反馈\n"
        f"summary: {json.dumps(summary, ensure_ascii=False)}\n"
        f"source: chat_feedback\n"
        f"{alias_line}"
        f"{assets_block}"
        f"{extra}"
        f"---\n"
        f"{body.strip()}\n"
    )
    out = entries_root / f"{eid}.md"
    out.write_text(content, encoding="utf-8")
    try:
        from improve import sync_active_project_to_library
        sync_active_project_to_library(root)
    except Exception:
        pass
    return out


def build_body(kind: str, text: str, style_fork: str | None) -> str:
    lines = [
        "**【来自 Cursor 对话的画师原话】**",
        f"> {text.strip()}",
        "",
    ]
    if kind == "style_redline":
        lines += [
            "## 红线（下次生图必须避开）",
            f"- ❌ 不要再出现：{text.strip()}",
            "- ✅ 对照本模块已有 `recipe` / 正例资产与色板。",
            "- Agent 生图前必须把本条写入 Negative / 约束说明。",
        ]
    elif kind == "recipe":
        lines += [
            "## 定稿（下次优先复用）",
            "- ✅ 画师确认「这版留着」——作为正向视觉锚点与可复现方向。",
            "- 后续同类题材优先沿用本张构图、色板与提示词方向。",
        ]
    elif kind == "visual_correction":
        lines += [
            "## 修正方向",
            f"- 按画师反馈调整：{text.strip()}",
        ]
        if style_fork:
            lines.append(f"- 检测到风格分叉意图 → 建议子模块后缀 `.{style_fork}`，与正比/其他画风隔离存放。")
    elif kind == "art_decision":
        lines += [
            "## 拍板",
            f"- 以后本模块统一遵循：{text.strip()}",
        ]
    else:
        lines.append(text.strip())
    return "\n".join(lines)


def cmd_feedback(
    root: Path,
    data: dict[str, Any],
    text: str,
    module: str = "",
    asset: str = "",
    kind: str = "",
    apply: bool = True,
    silent: bool = True,
    verbose: bool = False,
) -> int:
    if verbose:
        silent = False
    text = (text or "").strip()
    if not text:
        print("❌ 请传入画师原话，例如：python3 pmem_art.py feedback \"太赛博了，别这样画\" --module character.Astra")
        return 1

    detected = kind or detect_kind(text)
    style_fork = detect_style_fork(text) if detected == "visual_correction" else None
    mod = module or infer_module_from_text(text, data)

    # keep → approved；reject → rejected；其余 reference
    role = "reference"
    if detected == "recipe":
        role = "approved"
    elif detected == "style_redline":
        role = "rejected"

    summary = text.strip()
    if len(summary) > 80:
        summary = summary[:77] + "…"

    body = build_body(detected, text, style_fork)

    if not silent:
        print(f"🗣️  画师原话: {text}")
        print(f"📌 判定类型: {detected} ({KIND_META.get(detected, detected)})")
        print(f"📦 目标模块: {mod}")
        if style_fork:
            print(f"🎨 风格分叉: .{style_fork}")
        if asset:
            print(f"🖼️  关联资产: {asset} ({role})")

    if not apply:
        if not silent:
            print("（dry-run，未写入；加默认即写入，或显式 --apply）")
        return 0

    # 确保模块目录存在
    (root / ".memory-art" / "entries" / mod).mkdir(parents=True, exist_ok=True)

    path = write_memory_entry(
        root,
        module=mod,
        kind=detected,
        summary=summary,
        body=body,
        asset=asset,
        role=role,
        aliases=[style_fork] if style_fork else None,
        extra_meta={"style_fork": style_fork} if style_fork else None,
    )

    tip = None
    # High-signal: keep/reject/style → taste + knowledge + silent autopilot
    high_signal = detected in ("recipe", "style_redline", "visual_correction", "art_decision")
    try:
        from improve import (
            apply_feedback_to_taste,
            ingest_term_to_knowledge,
            run_silent_autopilot,
            compose_whisper_tip,
            try_consume_tip_budget,
            print_whisper_tip,
        )
        apply_feedback_to_taste(root, text, detected)
        cards = ingest_term_to_knowledge(root, text, source="feedback")
        if high_signal:
            auto = run_silent_autopilot(
                root,
                data,
                session_id=f"fb-{detected}",
                defects=text if detected == "style_redline" else "",
                strengths=text if detected == "recipe" else "",
                source="feedback",
                feedback_kind=detected,
                feedback_text=text,
                enqueue_learn=1,
            )
            tip = auto.get("tip")
        else:
            tip = compose_whisper_tip(feedback_kind=detected, feedback_text=text)
            if tip and not try_consume_tip_budget(root, f"feedback:{detected}:{text[:24]}"):
                tip = None
        if not silent:
            print(f"✅ 已写入记忆: {path.relative_to(root)}")
            if cards:
                print(f"🌍 知识广度扩展: {', '.join(cards)}")
            print("🎨 已同步强化个人口味档案 (.memory-art/_profile/taste.json)")
            print("💡 下次生同类图会自动召回，越画越准。")
        else:
            # Whisper only — tip budget exhausted ⇒ stay fully silent (no spam)
            if tip:
                print_whisper_tip(tip)
    except Exception as ex:
        if not silent:
            print(f"✅ 已写入记忆: {path.relative_to(root)}")
            print(f"⚠️ 口味/知识同步跳过: {ex}")
        else:
            print(f"「小提示」已记下")
    try:
        from pmem_art import refresh_atlas_silent
        refresh_atlas_silent(root)
    except Exception:
        pass
    return 0


def parse_feedback_from_stdin_or_hook(payload: dict[str, Any] | None = None) -> str:
    """Hook / Agent 可把用户最近一句塞进 JSON.user_message。"""
    if payload and isinstance(payload.get("user_message"), str):
        return payload["user_message"]
    return ""
