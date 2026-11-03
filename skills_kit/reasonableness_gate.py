"""出图前合理性闸门：提示词至少审核一次，并写出更合理的修订版。

对齐合成梯「先说通再出图」的成本模型：
- Agent 填清单 + 交 revised prompt
- CLI 做廉价启发式硬拦 + 写入会话
- converge generate 首轮无过闸则拒绝；过闸后默认注入 revised

不改动 ConvergeGate 的 9.5 / 满4轮 / 垫图规则；只把错误前提挡在 R1 之前。

逃生：`--skip-reasonableness-gate` 或环境变量 `PMEM_ART_SKIP_REASONABLENESS_GATE=1`
（仅调试；日常出图技能禁止跳过）。
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

# skill id → 必检清单键（Agent 必须逐条标 ok/fail）
SKILL_CHECKLISTS: dict[str, tuple[str, ...]] = {
    "ordinary": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
    ),
    "keyart": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "hero_read",
        "layout_not_style_echo",
    ),
    "clone": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "new_subject_not_ref_echo",
    ),
    "variant": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "only_named_delta",
    ),
    "split": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "role_separation",
    ),
    "shotpack": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "camera_sets_distinct",
    ),
    "ui": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "layout_zones",
        "no_content_clutter",
    ),
    "icon.a": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "safe_zone",
        "single_symbol",
    ),
    "icon.b": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "stroke_consistency",
    ),
    "icon.c": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "silhouette_read",
        "transparent_friendly",
    ),
    "merge": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "single_centered_item",
        "parts_add_concrete",
    ),
}

SKILL_ALIASES: dict[str, str] = {
    "draw": "ordinary",
    "普通图": "ordinary",
    "原画": "keyart",
    "key-art": "keyart",
    "key_art": "keyart",
    "克隆": "clone",
    "变体": "variant",
    "多图分工": "split",
    "镜头包": "shotpack",
    "界面": "ui",
    "hud": "ui",
    "icon": "icon.a",
    "icon_a": "icon.a",
    "icon-a": "icon.a",
    "图标a": "icon.a",
    "图标A": "icon.a",
    "appicon": "icon.a",
    "icon_b": "icon.b",
    "icon-b": "icon.b",
    "图标b": "icon.b",
    "图标B": "icon.b",
    "svg": "icon.b",
    "icon_c": "icon.c",
    "icon-c": "icon.c",
    "图标c": "icon.c",
    "图标C": "icon.c",
    "道具格": "icon.c",
    "合成梯": "merge",
    "merge-ladder": "merge",
    "merge_ladder": "merge",
}

CHECK_LABELS_ZH: dict[str, str] = {
    "subject_action": "主体在做什么/交付物是什么",
    "contact_scale": "接触关系与相对尺度",
    "element_budget": "元素预算（不堆景不过载）",
    "hard_locks": "硬锁（画幅/透明底/无字/机位等）",
    "fail_at_glance": "一眼失败条件已写明",
    "hero_read": "主视觉记忆点一眼可读",
    "layout_not_style_echo": "只借画风不借样张构图/机位/分区",
    "new_subject_not_ref_echo": "新题材，不回声参考主体",
    "only_named_delta": "只改点名的差分项",
    "role_separation": "多图身份/结构分工不串",
    "camera_sets_distinct": "镜头套差异够大",
    "layout_zones": "界面分区清楚",
    "no_content_clutter": "内容区不塞插画杂物",
    "safe_zone": "72%–80% 安全区",
    "single_symbol": "单符号高识别",
    "stroke_consistency": "线宽/端点一致",
    "silhouette_read": "厚剪影可读",
    "transparent_friendly": "透明底友好",
    "single_centered_item": "每档单件居中",
    "parts_add_concrete": "零件增量具体可画",
}

_CROWD_RE = re.compile(
    r"(灯串|村庄|远景|近景|中景|前景|背景|粒子|特效|光晕|光柱|"
    r"雪花纹|碎花|满屏|堆满|层层叠叠|village|bokeh|god.?rays|"
    r"particle|ornament.?flood)",
    re.I,
)
_SAFE_ZONE_RE = re.compile(r"(安全区|safe.?zone|72\s*%|80\s*%|72%-80%|72%–80%)", re.I)
_ICON_SQUARE_RE = re.compile(r"(1\s*:\s*1|1024|正方形|square|满幅)", re.I)
_UI_ZONE_RE = re.compile(r"(九宫格|顶栏|底栏|内容区|面板|弹窗|HUD|9-?slice|panel)", re.I)
_TRANSPARENT_RE = re.compile(r"(透明|transparent|alpha)", re.I)
_NO_TEXT_RE = re.compile(r"(无字|不要字|no\s*text|without\s*text|无可读)", re.I)
_SINGLE_ITEM_RE = re.compile(r"(单件|一件|居中|centered|single\s+item)", re.I)


def normalize_skill(skill: str) -> str:
    raw = (skill or "").strip()
    if not raw:
        return "ordinary"
    key = raw.lower().replace(" ", "")
    if key in SKILL_CHECKLISTS:
        return key
    if raw in SKILL_ALIASES:
        return SKILL_ALIASES[raw]
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    return key if key in SKILL_CHECKLISTS else "ordinary"


def default_checklist_template(skill: str) -> str:
    sk = normalize_skill(skill)
    keys = SKILL_CHECKLISTS.get(sk, SKILL_CHECKLISTS["ordinary"])
    return ";".join(f"{k}=ok" for k in keys)


def parse_checklist(text: str) -> dict[str, dict[str, str]]:
    """Parse `key=ok` / `key=fail:原因` / `key=ok:备注` 分号或换行分隔."""
    out: dict[str, dict[str, str]] = {}
    blob = (text or "").strip()
    if not blob:
        return out
    parts = re.split(r"[;\n]+", blob)
    for part in parts:
        piece = part.strip()
        if not piece or "=" not in piece:
            continue
        key, rest = piece.split("=", 1)
        key = key.strip()
        rest = rest.strip()
        if not key:
            continue
        if ":" in rest:
            status, note = rest.split(":", 1)
        else:
            status, note = rest, ""
        status_n = status.strip().lower()
        if status_n in ("ok", "pass", "true", "yes", "通过", "合理"):
            status_n = "ok"
        elif status_n in ("fail", "no", "false", "没过", "不合理", "bad"):
            status_n = "fail"
        else:
            status_n = "ok" if status_n == "" else "fail"
            note = rest
        out[key] = {"status": status_n, "note": note.strip()}
    return out


def _heuristic_issues(skill: str, draft: str, revised: str) -> list[str]:
    issues: list[str] = []
    d = (draft or "").strip()
    r = (revised or "").strip()
    if len(r) < 24:
        issues.append("revised 太短：修订提示词须写清主体、动作/布局与硬锁（至少约一句完整出图句）")
    if d and r and d == r and len(r) < 80:
        issues.append("revised 与 draft 完全相同且过短：请至少补上硬锁或元素预算，或把已合理处写完整")
    crowd_hits = _CROWD_RE.findall(r)
    if len(crowd_hits) >= 4 and not re.search(r"(只留|弱化|最多|减到|不要叠|预算)", r):
        issues.append(
            "元素预算可疑：修订句里堆景/特效词偏多且未写收敛预算（只留/弱化/最多…）"
        )
    if skill == "icon.a":
        if not _SAFE_ZONE_RE.search(r):
            issues.append("icon.a 缺安全区：修订句须含 72%–80% 安全区或 safe zone")
        if not _ICON_SQUARE_RE.search(r):
            issues.append("icon.a 缺画幅：修订句须点明 1:1 / 1024 / 满幅直角")
        if not _NO_TEXT_RE.search(r):
            issues.append("icon.a 缺无字：修订句须写死无字 / no text（母版禁止口号与小字）")
    if skill == "icon.c" and not _TRANSPARENT_RE.search(r):
        issues.append("icon.c 缺透明底：修订句须写透明底/transparent")
    if skill == "ui" and not _UI_ZONE_RE.search(r):
        issues.append("ui 缺分区：修订句须点名九宫格/顶栏底栏/内容区/面板等")
    if skill == "merge" and not _SINGLE_ITEM_RE.search(r):
        issues.append("merge 缺单件居中：修订句须写单件居中、非场景")
    if skill == "clone" and re.search(r"(同一[个位]?人|原角色再画|抄回参考主体)", r):
        issues.append("clone 疑似回声参考主体：换题材锁画风，不要把参考人画回来")
    if skill == "keyart" and re.search(
        r"(照着样张构图|同机位照抄|贴样张分区|沿用参考构图|构图跟参考一样)",
        r,
    ):
        issues.append(
            "keyart 疑似 layout 回声：只借画风，修订句须写清新机位/新分区，禁止贴样张构图"
        )
    if skill == "keyart" and not re.search(
        r"(新机位|换机位|不借构图|不贴样张构图|layout_not_style_echo|只借色板|只借画风)",
        r,
        re.I,
    ):
        # 有「参考/样张」字样却无反构图声明时硬拦
        if re.search(r"(参考|样张|风格图|垫图)", r):
            issues.append(
                "keyart 缺 layout_not_style_echo：有样张时修订句须写明只借画风、新机位/不贴样张构图"
            )
    return issues


def review_reasonableness(
    *,
    skill: str,
    draft: str,
    revised: str,
    checklist_text: str = "",
    notes: str = "",
    force_pass: bool = False,
) -> dict[str, Any]:
    """Return review payload. passed=False when checklist or heuristics fail."""
    sk = normalize_skill(skill)
    required = SKILL_CHECKLISTS.get(sk, SKILL_CHECKLISTS["ordinary"])
    parsed = parse_checklist(checklist_text)
    missing = [k for k in required if k not in parsed]
    failed_keys = [k for k, v in parsed.items() if k in required and v.get("status") != "ok"]
    heuristic = _heuristic_issues(sk, draft, revised)
    issues: list[str] = []
    if missing:
        issues.append(
            "清单未齐："
            + "、".join(f"{k}（{CHECK_LABELS_ZH.get(k, k)}）" for k in missing)
        )
    for k in failed_keys:
        note = (parsed.get(k) or {}).get("note") or ""
        label = CHECK_LABELS_ZH.get(k, k)
        issues.append(f"未过 {k}（{label}）" + (f"：{note}" if note else ""))
    if not force_pass:
        issues.extend(heuristic)
    elif len((revised or "").strip()) < 24:
        issues.append("即使 --force，revised 也不能为空壳")

    passed = len(issues) == 0
    checklist_out = {
        k: parsed.get(k) or {"status": "missing", "note": ""}
        for k in required
    }
    return {
        "passed": passed,
        "skill": sk,
        "draft_prompt": (draft or "").strip(),
        "revised_prompt": (revised or "").strip(),
        "checklist": checklist_out,
        "issues": issues,
        "notes": (notes or "").strip(),
        "force_pass": bool(force_pass),
        "reviewed_at": time.time(),
        "reviewed_at_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }


def apply_review_to_session(sess: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    """Persist review onto converge session dict (caller writes file)."""
    sess = dict(sess)
    history = list(sess.get("reasonableness_history") or [])
    history.append(
        {
            "reviewed_at": review.get("reviewed_at"),
            "passed": bool(review.get("passed")),
            "skill": review.get("skill"),
            "issues": list(review.get("issues") or []),
        }
    )
    sess["reasonableness_history"] = history[-8:]
    sess["reasonableness"] = {
        "passed": bool(review.get("passed")),
        "skill": review.get("skill"),
        "draft_prompt": review.get("draft_prompt"),
        "revised_prompt": review.get("revised_prompt"),
        "checklist": review.get("checklist"),
        "issues": list(review.get("issues") or []),
        "notes": review.get("notes") or "",
        "reviewed_at": review.get("reviewed_at"),
        "reviewed_at_iso": review.get("reviewed_at_iso"),
        "force_pass": bool(review.get("force_pass")),
    }
    notes = [d for d in list(sess.get("discussions") or []) if not (
        isinstance(d, dict) and d.get("kind") == "reasonableness"
    )]
    if review.get("passed"):
        chk = review.get("checklist") or {}
        ok_bits = [
            f"{k}=ok" + (f":{(chk[k] or {}).get('note')}" if (chk.get(k) or {}).get("note") else "")
            for k in chk
            if (chk.get(k) or {}).get("status") == "ok"
        ]
        notes.append(
            {
                "round": 0,
                "kind": "reasonableness",
                "prompt": str(review.get("revised_prompt") or ""),
                "strengths": "合理性闸已过：" + ("；".join(ok_bits) if ok_bits else "清单齐全"),
                "defects": "",
                "next_fix": "首轮 generate 使用本修订提示词；审美迭代不得推翻硬锁与元素预算",
            }
        )
    notes.sort(key=lambda d: int(d.get("round") or 0))
    sess["discussions"] = notes
    return sess


def check_reasonableness_gate(
    sess: dict[str, Any],
    *,
    round_num: int = 1,
    prompt: str = "",
) -> tuple[bool, str, str]:
    """Return (ok, message, prompt_to_use).

    Any generate is blocked until the session has a passed reasonableness review
    (closes the ``--round 2`` skip loophole). Prompt injection of ``revised``
    only happens on the first generate; later rounds keep caller ``--prompt``
    (typically revised + next_fix).
    """
    del round_num  # round number must not decide whether the gate applies
    blob = sess.get("reasonableness") if isinstance(sess.get("reasonableness"), dict) else None
    if not blob or not blob.get("passed"):
        issues = ""
        if blob and blob.get("issues"):
            issues = " 上次未过：" + "；".join(str(x) for x in blob.get("issues")[:4])
        return (
            False,
            "出图前缺少已通过的合理性审核。请先：\n"
            "  python3 pmem_art.py reasonableness review --id <session> "
            "--skill <ordinary|keyart|clone|variant|split|ui|icon.a|icon.b|icon.c|merge> "
            "--draft \"<草稿提示词>\" --revised \"<更合理的提示词>\" "
            "--checklist \"subject_action=ok;contact_scale=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok\"\n"
            "审核须同时给出 revised；过闸后再 converge generate。"
            f"{issues}",
            "",
        )

    rounds = list(sess.get("rounds") or [])
    has_prior_image = any(str(r.get("image") or "").strip() for r in rounds)
    incoming = (prompt or "").strip()
    revised = str(blob.get("revised_prompt") or "").strip()
    draft = str(blob.get("draft_prompt") or "").strip()

    # Later rounds: keep caller prompt (usually revised + next_fix). Empty → fall back.
    if has_prior_image:
        if incoming:
            return True, "合理性闸已在本会话通过，沿用本轮 --prompt", incoming
        if revised:
            return True, "非首轮未给 --prompt，回退到合理性修订提示词", revised
        return True, "合理性闸已在本会话通过（无 revised 可回退）", incoming

    # First generate: always ship the reviewed revised text.
    # Prevents rubber-stamp review then swapping in an unreviewed prompt.
    if not revised:
        return (
            False,
            "合理性记录 passed 但 revised 为空，请重跑 reasonableness review。",
            "",
        )
    if not incoming or incoming == draft or incoming == revised:
        msg = "已注入合理性修订提示词" if incoming != revised else "合理性闸已过，使用 revised"
        return True, msg, revised
    return True, "首轮强制使用合理性 revised（已忽略未再审的 --prompt；若要改提示词请重跑 review）", revised


def format_review_print(review: dict[str, Any]) -> str:
    sk = review.get("skill")
    lines = [
        f"{'✅' if review.get('passed') else '❌'} [合理性闸 · {sk}] "
        f"{'通过' if review.get('passed') else '未通过'}",
    ]
    chk = review.get("checklist") or {}
    for k, v in chk.items():
        st = (v or {}).get("status") or "?"
        note = (v or {}).get("note") or ""
        mark = "✓" if st == "ok" else ("·" if st == "missing" else "✗")
        lines.append(f"  {mark} {k}（{CHECK_LABELS_ZH.get(k, k)}）{(' · ' + note) if note else ''}")
    for issue in review.get("issues") or []:
        lines.append(f"  · {issue}")
    if review.get("passed"):
        rev = str(review.get("revised_prompt") or "")
        lines.append("修订提示词（generate 将优先用这句）：")
        lines.append(rev if len(rev) <= 500 else rev[:500] + "…")
    else:
        lines.append("请按未过项改 revised / checklist 后重跑 review，禁止跳过直接 generate。")
    return "\n".join(lines)


def cmd_reasonableness_at_root(
    root: Path,
    *,
    action: str = "review",
    session_id: str = "latest",
    skill: str = "ordinary",
    draft: str = "",
    revised: str = "",
    checklist: str = "",
    notes: str = "",
    force: bool = False,
) -> int:
    from .converge import _session_file, _write_session_json

    action_n = (action or "review").strip().lower()
    sf = _session_file(root, session_id)
    if action_n == "show":
        if not sf.is_file():
            print(f"❌ 未找到会话 `{session_id}`")
            return 1
        sess = json.loads(sf.read_text(encoding="utf-8"))
        blob = sess.get("reasonableness")
        if not isinstance(blob, dict):
            print("尚无合理性审核记录。")
            return 1
        print(format_review_print({**blob, "passed": bool(blob.get("passed"))}))
        return 0 if blob.get("passed") else 1

    if action_n == "template":
        sk = normalize_skill(skill)
        print(f"skill={sk}")
        print(default_checklist_template(sk))
        for k in SKILL_CHECKLISTS.get(sk, SKILL_CHECKLISTS["ordinary"]):
            print(f"  - {k}: {CHECK_LABELS_ZH.get(k, k)}")
        return 0

    if action_n != "review":
        print("reasonableness 只支持 review | show | template")
        return 2

    if not sf.is_file():
        print(
            f"❌ 未找到收敛会话 `{session_id}`。请先 converge start，再跑合理性审核。\n"
            f"   python3 pmem_art.py converge start --id {session_id} --goal ..."
        )
        return 1
    if not (revised or "").strip():
        print("❌ reasonableness review 需要 --revised（审核同时必须给出更合理的提示词）")
        return 1
    if not (draft or "").strip():
        print("❌ reasonableness review 需要 --draft（先写草稿，再给 revised）")
        return 1

    review = review_reasonableness(
        skill=skill,
        draft=draft,
        revised=revised,
        checklist_text=checklist,
        notes=notes,
        force_pass=force,
    )
    sess = json.loads(sf.read_text(encoding="utf-8"))
    # Always persist latest attempt (passed flag tells generate whether to unlock).
    sess = apply_review_to_session(sess, review)
    _write_session_json(sf, sess)
    print(format_review_print(review))
    if review.get("passed"):
        print(
            f"已写入会话 `{session_id}`。"
            "下一步用 revised 做 converge generate（可省略 --prompt，将自动注入）。"
        )
        return 0
    print("已写入会话（passed=false）；generate 仍会被拦截，请按未过项改 revised/checklist 后重跑 review。")
    return 1
