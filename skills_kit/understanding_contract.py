"""理解合同（外置）+ 每轮最小工作集 + 反馈归层。

目标：美术话糊时冻住「系统当前理解」，多轮只注入最小包，减少聊天考古导致的漂移。
不改动 route 闸 / 9.5 / 4 轮 / 垫图 / 续写硬约束（表一-A）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .platform_cli import pmem_art_cli

CONTRACT_VERSION = 1

# L0：换品类 / 重开 / 路由纠偏（毁约级）
# 与 install.py「跑偏纠偏」口语触发词保持同向；补「不符合」等常见否词，避免只靠「不对」漏网。
_L0_PATTERNS = (
    r"不对",
    r"错了",
    r"不行",
    r"不是这样",
    r"理解错了",
    r"搞错了",
    r"偏了",
    r"跑偏",
    r"跑歪",
    r"离题",
    r"答非所问",
    r"不符合",
    r"对不上",
    r"差太远",
    r"不是我想要的",
    r"不是我要的",
    r"没按我说的",
    r"跟我说的不一样",
    r"画错了",
    r"做错了",
    r"不是这个意思",
    r"不是这个效果",
    r"翻车了",
    r"重做",
    r"重来",
    r"推倒",
    r"另起炉灶",
    r"从零",
    r"重新分析",
    r"重新想",
    r"不要沿用",
    r"别沿用",
    r"忘掉上轮",
    r"历史作废",
    r"刚才那套作废",
    r"上一套作废",
    r"全部作废",
    r"这套作废",
    r"整套作废",
    r"换条路",
    r"换个思路",
    r"换方案",
    r"别按刚才",
    r"别按旧的",
    r"不要按旧方案",
    r"不要接着改",
    r"不是这个技能",
    r"走错技能",
    r"重新路由",
    r"不该走",
    r"我要的是界面",
    r"我要的是图标",
    r"我要的是合成",
    r"不是插画",
    r"不是单张",
)

# L1：锁点边界（升版合同，不重开品类）
_L1_PATTERNS = (
    r"锁住",
    r"锁定",
    r"别动",
    r"不要动",
    r"不准改",
    r"机位不要",
    r"别改机位",
    r"身份别",
    r"脸别",
    r"画风锁",
    r"风格锁",
    r"保持机位",
    r"保持身份",
    r"构图别动",
    r"以后都用",
    r"往后都用",
)

# L2：表面微调（默认落点）
_L2_PATTERNS = (
    r"好看",
    r"高级",
    r"有感觉",
    r"精致",
    r"再.+一点",
    r"稍微",
    r"微调",
    r"修一下",
    r"手",
    r"指",
    r"颜色",
    r"暖一点",
    r"冷一点",
    r"亮一点",
    r"暗一点",
    r"大一点",
    r"小一点",
    r"继续收敛",
    r"下一轮",
    r"这版留着",
)


def empty_contract() -> dict[str, Any]:
    return {
        "version": CONTRACT_VERSION,
        "raw_utterance": "",
        "l0": {
            "route_ids": [],
            "banner": "",
            "delivery": "",
        },
        "l1": {
            "locks": [],
            "unlocks": [],
            "defaults_shown": [],
            "commercial_vibe": "",
        },
        "l2": {
            "open": True,
            "surface_fix": "",
            "last_feedback": "",
            "feedback_layer": "",
        },
        "notes": "",
    }


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"[,;；、|\n]+", value)
        return [p.strip() for p in parts if p.strip()]
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            s = str(item or "").strip()
            if s:
                out.append(s)
        return out
    s = str(value).strip()
    return [s] if s else []


def _uniq(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def build_contract(
    *,
    raw_utterance: str = "",
    route_ids: list[str] | None = None,
    banner: str = "",
    delivery: str = "",
    locks: list[str] | str | None = None,
    unlocks: list[str] | str | None = None,
    defaults_shown: list[str] | str | None = None,
    commercial_vibe: str = "",
    surface_fix: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Build understanding contract v1 (soft lock of current interpretation)."""
    c = empty_contract()
    c["raw_utterance"] = str(raw_utterance or "").strip()
    c["l0"]["route_ids"] = _uniq([str(x) for x in (route_ids or []) if str(x).strip()])
    c["l0"]["banner"] = str(banner or "").strip()
    c["l0"]["delivery"] = str(delivery or "").strip()
    c["l1"]["locks"] = _uniq(_as_list(locks))
    c["l1"]["unlocks"] = _uniq(_as_list(unlocks))
    c["l1"]["defaults_shown"] = _uniq(_as_list(defaults_shown))
    c["l1"]["commercial_vibe"] = str(commercial_vibe or "").strip()
    c["l2"]["surface_fix"] = str(surface_fix or "").strip()
    c["notes"] = str(notes or "").strip()
    return c


def contract_from_session_bootstrap(
    *,
    goal: str = "",
    route_ids: list[str] | None = None,
    banner: str = "",
    advise: dict[str, Any] | None = None,
    defaults_shown: list[str] | str | None = None,
    locks: list[str] | str | None = None,
    unlocks: list[str] | str | None = None,
    commercial_vibe: str = "",
    delivery: str = "",
) -> dict[str, Any]:
    adv = advise if isinstance(advise, dict) else {}
    ids = list(route_ids or [])
    if not ids:
        ids = [str(x) for x in (adv.get("route_ids") or []) if str(x).strip()]
    ban = str(banner or adv.get("banner") or adv.get("artist_say") or "").strip()
    deliv = str(delivery or "").strip()
    if not deliv and ids:
        deliv = str(ids[0])
    artist = str(adv.get("artist_say") or "").strip()
    raw = str(goal or "").strip() or artist
    return build_contract(
        raw_utterance=raw,
        route_ids=ids,
        banner=ban,
        delivery=deliv,
        locks=locks,
        unlocks=unlocks,
        defaults_shown=defaults_shown,
        commercial_vibe=commercial_vibe,
    )


def format_contract_summary(contract: dict[str, Any] | None) -> str:
    c = contract if isinstance(contract, dict) else empty_contract()
    l0 = c.get("l0") if isinstance(c.get("l0"), dict) else {}
    l1 = c.get("l1") if isinstance(c.get("l1"), dict) else {}
    l2 = c.get("l2") if isinstance(c.get("l2"), dict) else {}
    lines = [
        f"理解合同 v{c.get('version') or CONTRACT_VERSION}",
        f"原话/目标：{(c.get('raw_utterance') or '（空）')[:160]}",
        f"L0 交付：{l0.get('delivery') or '（未标）'} | route_ids={','.join(l0.get('route_ids') or []) or '—'}",
    ]
    if l0.get("banner"):
        lines.append(f"banner：{str(l0.get('banner'))[:120]}")
    locks = l1.get("locks") or []
    unlocks = l1.get("unlocks") or []
    lines.append(f"L1 锁：{'；'.join(locks) if locks else '（未写，可后补）'}")
    lines.append(f"L1 不锁：{'；'.join(unlocks) if unlocks else '（未写）'}")
    defaults = l1.get("defaults_shown") or []
    if defaults:
        lines.append("本趟默认：" + "｜".join(str(x) for x in defaults))
    else:
        lines.append("本趟默认：（尚未写入「默认：…」——建议补上让美术看见）")
    vibe = str(l1.get("commercial_vibe") or "").strip()
    if vibe:
        lines.append(f"商业气质：{vibe}")
    fix = str(l2.get("surface_fix") or "").strip()
    lines.append(f"L2 当轮可改：{fix or '（看图后单点写）'}")
    return "\n".join(lines)


def defaults_visibility_ok(contract: dict[str, Any] | None) -> tuple[bool, str]:
    """True when defaults_shown is non-empty (agent showed soft defaults to artist)."""
    c = contract if isinstance(contract, dict) else {}
    l1 = c.get("l1") if isinstance(c.get("l1"), dict) else {}
    shown = [str(x).strip() for x in (l1.get("defaults_shown") or []) if str(x).strip()]
    if shown:
        return True, "已写默认：" + "｜".join(shown)
    return False, "未写「默认：…」。糊需求时请补 defaults，避免美术看不见系统听成了啥。"


def classify_feedback(text: str) -> dict[str, Any]:
    """Heuristic layer for artist feedback. Default L2 when unclear."""
    raw = str(text or "").strip()
    if not raw:
        return {"layer": "l2", "reason": "empty→default_l2", "text": ""}
    for pat in _L0_PATTERNS:
        if re.search(pat, raw):
            return {"layer": "l0", "reason": f"hit:{pat}", "text": raw}
    for pat in _L1_PATTERNS:
        if re.search(pat, raw):
            return {"layer": "l1", "reason": f"hit:{pat}", "text": raw}
    for pat in _L2_PATTERNS:
        if re.search(pat, raw):
            return {"layer": "l2", "reason": f"hit:{pat}", "text": raw}
    return {"layer": "l2", "reason": "default_surface", "text": raw}


def apply_feedback(contract: dict[str, Any], feedback: str) -> dict[str, Any]:
    """Patch contract by classified layer. L0 only marks note — does not auto-reroute."""
    c = json.loads(json.dumps(contract if isinstance(contract, dict) else empty_contract()))
    hit = classify_feedback(feedback)
    layer = hit["layer"]
    text = hit["text"]
    l2 = c.setdefault("l2", {})
    if not isinstance(l2, dict):
        l2 = {}
        c["l2"] = l2
    l2["last_feedback"] = text
    l2["feedback_layer"] = layer
    if layer == "l2":
        l2["surface_fix"] = text
        l2["open"] = True
    elif layer == "l1":
        l1 = c.setdefault("l1", {})
        if not isinstance(l1, dict):
            l1 = {}
            c["l1"] = l1
        # 整句进 notes；locks 只收短标签，避免工作集被长句刷屏
        short = text
        tags: list[str] = []
        for key in ("机位", "身份", "画风", "风格", "构图", "脸"):
            if key in text:
                tags.append(f"保持{key}")
        if not tags:
            short = text if len(text) <= 24 else text[:24]
            tags = [short]
        l1["locks"] = _uniq(_as_list(l1.get("locks")) + tags)
        note = str(c.get("notes") or "")
        c["notes"] = (note + f"\n[L1升版] {text}").strip()
    else:
        note = str(c.get("notes") or "")
        c["notes"] = (note + f"\n[L0需重开/确认] {text}").strip()
    return c


def merge_contract_fields(
    contract: dict[str, Any],
    *,
    defaults_shown: list[str] | str | None = None,
    locks: list[str] | str | None = None,
    unlocks: list[str] | str | None = None,
    commercial_vibe: str | None = None,
    surface_fix: str | None = None,
    raw_utterance: str | None = None,
    banner: str | None = None,
    delivery: str | None = None,
    route_ids: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    c = json.loads(json.dumps(contract if isinstance(contract, dict) else empty_contract()))
    if raw_utterance is not None:
        c["raw_utterance"] = str(raw_utterance).strip()
    l0 = c.setdefault("l0", {})
    if not isinstance(l0, dict):
        l0 = {}
        c["l0"] = l0
    if banner is not None:
        l0["banner"] = str(banner).strip()
    if delivery is not None:
        l0["delivery"] = str(delivery).strip()
    if route_ids is not None:
        l0["route_ids"] = _uniq([str(x) for x in route_ids if str(x).strip()])
    l1 = c.setdefault("l1", {})
    if not isinstance(l1, dict):
        l1 = {}
        c["l1"] = l1
    if defaults_shown is not None:
        l1["defaults_shown"] = _uniq(_as_list(defaults_shown))
    if locks is not None:
        l1["locks"] = _uniq(_as_list(locks))
    if unlocks is not None:
        l1["unlocks"] = _uniq(_as_list(unlocks))
    if commercial_vibe is not None:
        l1["commercial_vibe"] = str(commercial_vibe).strip()
    l2 = c.setdefault("l2", {})
    if not isinstance(l2, dict):
        l2 = {}
        c["l2"] = l2
    if surface_fix is not None:
        l2["surface_fix"] = str(surface_fix).strip()
    if notes is not None:
        c["notes"] = str(notes).strip()
    c["version"] = CONTRACT_VERSION
    return c


def format_working_set(
    contract: dict[str, Any] | None,
    *,
    session_id: str = "",
    image: str = "",
    score: float | None = None,
    defects: str = "",
    next_fix: str = "",
) -> str:
    """Minimal per-round pack for the agent — not the full chat archaeology."""
    c = contract if isinstance(contract, dict) else empty_contract()
    l0 = c.get("l0") if isinstance(c.get("l0"), dict) else {}
    l1 = c.get("l1") if isinstance(c.get("l1"), dict) else {}
    l2 = c.get("l2") if isinstance(c.get("l2"), dict) else {}
    fix = str(next_fix or l2.get("surface_fix") or "").strip() or "（看图后只写一处）"
    lines = [
        "【每轮最小工作集】只准用下面这些做下一刀；禁止靠长聊天重谈 L0/L1。",
        f"session：{session_id or '—'}",
        f"L0：{l0.get('delivery') or '—'} | {','.join(l0.get('route_ids') or []) or '—'}",
        f"L1 锁：{'；'.join(l1.get('locks') or []) or '（未写）'}",
        f"L1 不锁：{'；'.join(l1.get('unlocks') or []) or '（未写）'}",
    ]
    defaults = l1.get("defaults_shown") or []
    if defaults:
        lines.append("默认：" + "｜".join(str(x) for x in defaults))
    vibe = str(l1.get("commercial_vibe") or "").strip()
    if vibe:
        lines.append(f"商业气质：{vibe}")
    if image:
        lines.append(f"本图：{image}")
    if score is not None:
        try:
            lines.append(f"上轮分：{float(score):.2f}")
        except (TypeError, ValueError):
            pass
    if defects:
        lines.append(f"主缺陷：{str(defects).strip()[:200]}")
    lines.append(f"只改一处：{fix[:200]}")
    lines.append(
        f"查合同：`{pmem_art_cli()} contract show --id {session_id or '<session>'}`"
    )
    return "\n".join(lines)


def ensure_session_contract(sess: dict[str, Any]) -> dict[str, Any]:
    """Single source for missing/legacy sessions (show 与 working-set 同构)."""
    ids = [str(x) for x in (sess.get("route_ids") or []) if str(x)]
    split_hint = str(sess.get("contract") or "").strip()
    fallback_delivery = str(ids[0]) if ids else (split_hint if split_hint else "")
    existing = sess.get("understanding_contract")
    if isinstance(existing, dict) and existing.get("version"):
        # 残缺合同：用会话字段补 L0，不覆盖已有非空值
        fixed = json.loads(json.dumps(existing))
        l0 = fixed.setdefault("l0", {})
        if not isinstance(l0, dict):
            l0 = {}
            fixed["l0"] = l0
        if not l0.get("route_ids") and ids:
            l0["route_ids"] = ids
        if not str(l0.get("delivery") or "").strip() and fallback_delivery:
            l0["delivery"] = fallback_delivery
        if not str(fixed.get("raw_utterance") or "").strip() and sess.get("goal"):
            fixed["raw_utterance"] = str(sess.get("goal") or "").strip()
        return fixed
    return contract_from_session_bootstrap(
        goal=str(sess.get("goal") or ""),
        route_ids=ids,
        delivery=fallback_delivery,
    )


def working_set_from_session(sess: dict[str, Any], session_id: str = "") -> str:
    rounds = list(sess.get("rounds") or [])
    image = ""
    score: float | None = None
    defects = ""
    next_fix = ""
    judged = [r for r in rounds if r.get("judged")]
    if judged:
        row = judged[-1]
        image = str(row.get("image") or "")
        try:
            score = float(row.get("score"))
        except (TypeError, ValueError):
            score = None
        defects = str(row.get("defects") or "")
        next_fix = str(row.get("next_fix") or "")
    elif rounds:
        row = rounds[-1]
        image = str(row.get("image") or "")
    contract = ensure_session_contract(sess)
    return format_working_set(
        contract,
        session_id=session_id or str(sess.get("session_id") or ""),
        image=image,
        score=score,
        defects=defects,
        next_fix=next_fix,
    )


def resolve_contract_session_id(root: Path, session_id: str) -> tuple[str, str]:
    """Map bare `latest` to active converge cell when possible. Returns (sid, note)."""
    sid = (session_id or "latest").strip() or "latest"
    if sid != "latest":
        return sid, ""
    try:
        from .converge_loop import active_session_id

        active = str(active_session_id(root) or "").strip()
    except Exception:
        active = ""
    if active and active != "latest":
        return active, f"未带 --session，已改绑活跃会话 `{active}`"
    return sid, ""


def _session_path(root: Path, session_id: str) -> Path:
    sid = (session_id or "latest").strip() or "latest"
    if any(ch in sid for ch in "/\\:\0"):
        raise ValueError(f"非法 session id: {sid}")
    return Path(root) / ".memory-art" / "converge" / f"{sid}.json"


def load_session_contract(
    root: Path, session_id: str, *, persist_if_missing: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = _session_path(root, session_id)
    if not path.is_file():
        raise FileNotFoundError(f"会话不存在: {path}")
    sess = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(sess, dict):
        raise ValueError("会话 JSON 损坏")
    had = isinstance(sess.get("understanding_contract"), dict)
    contract = ensure_session_contract(sess)
    if persist_if_missing and not had:
        sess["understanding_contract"] = contract
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    return sess, contract


def save_session_contract(root: Path, session_id: str, contract: dict[str, Any]) -> Path:
    path = _session_path(root, session_id)
    sess = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(sess, dict):
        raise ValueError("会话 JSON 损坏")
    sess["understanding_contract"] = contract
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def cmd_contract(
    root: Path,
    *,
    action: str,
    session_id: str = "latest",
    defaults: str = "",
    locks: str = "",
    unlocks: str = "",
    commercial_vibe: str = "",
    surface_fix: str = "",
    feedback: str = "",
    text: str = "",
    json_out: bool = False,
) -> int:
    action = (action or "show").strip().lower()
    sid, remap_note = resolve_contract_session_id(root, session_id or "latest")
    if remap_note and action != "classify":
        print(f"ℹ️ {remap_note}")

    if action == "classify":
        hit = classify_feedback(text or feedback)
        if json_out:
            print(json.dumps(hit, ensure_ascii=False))
        else:
            print(f"layer={hit['layer']} reason={hit['reason']}\n{hit['text']}")
        return 0

    try:
        # show/working-set/defaults-check：旧会话缺字段时懒写入，避免磁盘与 CLI 两套真相
        persist = action in ("show", "working-set", "defaults-check")
        sess, contract = load_session_contract(root, sid, persist_if_missing=persist)
    except (OSError, ValueError, json.JSONDecodeError, FileNotFoundError) as exc:
        print(f"❌ {exc}")
        if (session_id or "").strip() in ("", "latest"):
            print(
                f"   提示：请带上 `--id <本任务session>`，或先 "
                f"`{pmem_art_cli()} converge start --id <id> …`。"
            )
        return 1

    if action == "show":
        if json_out:
            print(json.dumps(contract, ensure_ascii=False, indent=2))
        else:
            print(format_contract_summary(contract))
            ok, msg = defaults_visibility_ok(contract)
            print(("✅ " if ok else "⚠️ ") + msg)
        return 0

    if action == "working-set":
        pack = working_set_from_session(sess, session_id=sid)
        if json_out:
            print(json.dumps({"working_set": pack, "contract": contract}, ensure_ascii=False))
        else:
            print(pack)
        return 0

    if action == "defaults-check":
        ok, msg = defaults_visibility_ok(contract)
        print(("✅ " if ok else "⚠️ ") + msg)
        return 0 if ok else 2

    if action == "set":
        kwargs: dict[str, Any] = {}
        if defaults:
            kwargs["defaults_shown"] = defaults
        if locks:
            kwargs["locks"] = locks
        if unlocks:
            kwargs["unlocks"] = unlocks
        if commercial_vibe:
            kwargs["commercial_vibe"] = commercial_vibe
        if surface_fix:
            kwargs["surface_fix"] = surface_fix
        if not kwargs:
            print("❌ set 至少提供 --defaults / --locks / --unlocks / --vibe / --surface-fix 之一")
            return 1
        contract = merge_contract_fields(contract, **kwargs)
        save_session_contract(root, sid, contract)
        print(format_contract_summary(contract))
        ok, msg = defaults_visibility_ok(contract)
        print(("✅ " if ok else "⚠️ ") + msg)
        return 0

    if action == "patch":
        fb = feedback or text
        if not fb.strip():
            print("❌ patch 需要 --feedback 或 --text")
            return 1
        contract = apply_feedback(contract, fb)
        save_session_contract(root, sid, contract)
        hit = classify_feedback(fb)
        print(f"已归层 {hit['layer']}（{hit['reason']}）")
        print(format_contract_summary(contract))
        if hit["layer"] == "l0":
            print("⚠️ L0 反馈：请确认是否换交付/重开；不要只当微调继续画。")
        return 0

    print(f"❌ 未知 action: {action}（show|set|patch|working-set|defaults-check|classify）")
    return 1
