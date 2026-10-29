"""路由话术库：本地检索 + 规则分流，禁止把整库塞进大模型上下文。

资产分三层：
1. 规则：`plan_route`（准绳）
2. 原型/难例库：短句 + 标签，本地 top-k 检索
3. 混淆卡：几十字的易混提示，按关键词命中后附带

用户扩技能时可将正负例追加到项目
`.memory-art/route_bank/user.jsonl`；安装时重建打包库。
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .agent_route_cases import Case, build_cases
from .agent_router import Plan, plan_route
from .route_ask import artist_detail_for, artist_say_for, detect_vague_ask
from .route_normalize import build_canonical_brief, expand_colloquial

# 每条路由保留的原型上限（组合生成会去重）
_PROTOTYPE_CAP = 24
# 难例桶：整桶保留（易混 / 停机 / heldout）
_HARD_BUCKETS = frozenset(
    {
        "heldout",
        "hard",
        "icon_conflict",
        "icon_unspecified",
        "unrecognized",
        "pixels",
        "showcase_empty",
        "named_unknown",
        "negated_ban",
        "not_variant",
        "not_lens",
        "ref_same_person",
        "ordinary_two_refs",
        "single_popup",
        "prompt_then_draw",
        "critique_then_draw",
        "multi_states",
    }
)

CONFUSION_CARDS: list[dict[str, str]] = [
    {
        "id": "ref_no_new_subject",
        "when": "有参考但没说新题材、新物件、新角色",
        "tip": "普通图，不进克隆。",
        "keywords": "参考|照这张|按这张|别换题材|还是画这个",
    },
    {
        "id": "no_lens_pack",
        "when": "没人要几套机位 / 镜头包",
        "tip": "不要进镜头包；「镜头感强一点」仍是普通图。",
        "keywords": "镜头感|只要一张|一张半身",
    },
    {
        "id": "single_not_kit",
        "when": "单张弹框或只要一张图标",
        "tip": "不升成整套界面或图标集。",
        "keywords": "就一张|一张空弹|不要整套|画一个图标",
    },
    {
        "id": "clone_needs_new",
        "when": "有参考并且要换新题材",
        "tip": "锁画风，走克隆。",
        "keywords": "换成|别画原来|主体改成|换题材",
    },
    {
        "id": "variant_same_id",
        "when": "同一身份换表情/动作/画风，机位已在图上",
        "tip": "走变体，不走多图分工。",
        "keywords": "表情|差分|换个画风|同一张脸",
    },
    {
        "id": "multi_split_roles",
        "when": "两张图各管一件事，或关开态机位与身份不在同一张",
        "tip": "走多图分工；关开写成前后两行。",
        "keywords": "各管一件事|第一张是脸|关上|打开|身份在第一张",
    },
    {
        "id": "icon_abc",
        "when": "图标 A/B/C 同时命中或只说「图标」",
        "tip": "停下来只问这一处，不替玩家挑。",
        "keywords": "桌面图标|线性 svg|背包|画一个图标|1024",
    },
    {
        "id": "default_ordinary",
        "when": "专技都没对上、就是要画一张",
        "tip": "【走默认路径】普通图；单张 medium，≤4 轮，≥9.50。",
        "keywords": "画一张|出一张|来一张",
    },
]

_PACKAGED_NAME = "route_bank.jsonl"
_USER_NAME = "user.jsonl"


@dataclass
class BankEntry:
    text: str
    mode: str
    route_ids: list[str] = field(default_factory=list)
    bucket: str = ""
    reason: str = ""
    images: int = 0
    hard: bool = False
    source: str = "packaged"  # packaged | user

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def packaged_bank_path() -> Path:
    return Path(__file__).resolve().parent / "data" / _PACKAGED_NAME


def project_bank_dir(root: Path) -> Path:
    return Path(root) / ".memory-art" / "route_bank"


def user_bank_path(root: Path) -> Path:
    return project_bank_dir(root) / _USER_NAME


def _tokens(text: str) -> Counter[str]:
    raw = (text or "").strip().lower()
    raw = re.sub(r"\s+", "", raw)
    toks: list[str] = []
    # 汉字/词块 + 英文数字片段
    for m in re.finditer(r"[\u4e00-\u9fff]{1,}|[a-z0-9_\-/]+", raw):
        piece = m.group(0)
        if re.fullmatch(r"[\u4e00-\u9fff]+", piece):
            if len(piece) == 1:
                toks.append(piece)
            else:
                toks.extend(piece[i : i + 2] for i in range(len(piece) - 1))
                if len(piece) >= 3:
                    toks.extend(piece[i : i + 3] for i in range(len(piece) - 2))
        else:
            toks.append(piece)
    return Counter(toks)


def _score(query: Counter[str], doc: Counter[str]) -> float:
    if not query or not doc:
        return 0.0
    # 加权重叠 + 轻度长度归一，避免长句霸榜
    overlap = 0.0
    for t, qn in query.items():
        if t in doc:
            overlap += qn * (1.0 + math.log1p(doc[t]))
    if overlap <= 0:
        return 0.0
    return overlap / math.sqrt(sum(query.values()) * max(1.0, math.sqrt(sum(doc.values()))))


def _case_to_entry(case: Case, *, source: str = "packaged") -> BankEntry:
    hard = case.bucket in _HARD_BUCKETS or case.mode == "stop" or case.bucket == "heldout"
    return BankEntry(
        text=case.text,
        mode=case.mode,
        route_ids=list(case.route_ids),
        bucket=case.bucket,
        reason=case.reason or "",
        images=len(case.images or []),
        hard=hard,
        source=source,
    )


def distill_entries(cases: Iterable[Case] | None = None) -> list[BankEntry]:
    """从 2500+ 组合用例蒸馏：难例全留 + 每路由原型上限。"""
    cases = list(cases if cases is not None else build_cases())
    by_route: dict[str, list[BankEntry]] = defaultdict(list)
    hard: list[BankEntry] = []
    seen: set[str] = set()

    for case in cases:
        key = case.text.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        entry = _case_to_entry(case)
        if entry.hard:
            hard.append(entry)
            continue
        rid = ",".join(entry.route_ids) or entry.mode
        by_route[rid].append(entry)

    out = list(hard)
    for rid, items in by_route.items():
        # 均匀抽样：头尾 + 步进
        if len(items) <= _PROTOTYPE_CAP:
            out.extend(items)
            continue
        step = max(1, len(items) // _PROTOTYPE_CAP)
        picked = items[::step][:_PROTOTYPE_CAP]
        out.extend(picked)
    return out


def write_bank(entries: list[BankEntry], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ent in entries:
            fh.write(json.dumps(ent.to_dict(), ensure_ascii=False) + "\n")
    return path


def load_jsonl(path: Path) -> list[BankEntry]:
    if not path.is_file():
        return []
    out: list[BankEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        out.append(
            BankEntry(
                text=str(raw.get("text") or ""),
                mode=str(raw.get("mode") or ""),
                route_ids=list(raw.get("route_ids") or []),
                bucket=str(raw.get("bucket") or ""),
                reason=str(raw.get("reason") or ""),
                images=int(raw.get("images") or 0),
                hard=bool(raw.get("hard")),
                source=str(raw.get("source") or "packaged"),
            )
        )
    return out


def rebuild_packaged_bank() -> Path:
    entries = distill_entries()
    return write_bank(entries, packaged_bank_path())


def sync_project_bank(root: Path) -> Path:
    """安装时：把打包库拷到项目 .memory-art/route_bank/，保留 user.jsonl。

    仅当打包库不存在于项目，或打包库 mtime ≥ 项目拷贝时才覆盖，
    避免较新的项目库被旧打包库盖回。
    """
    dest_dir = project_bank_dir(root)
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = packaged_bank_path()
    if not src.is_file():
        rebuild_packaged_bank()
    dest = dest_dir / _PACKAGED_NAME
    should_copy = True
    if dest.is_file() and src.is_file():
        should_copy = src.stat().st_mtime >= dest.stat().st_mtime
    if should_copy:
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    user = user_bank_path(root)
    if not user.exists():
        user.write_text(
            "# 用户追加的路由话术（JSONL）。每行: "
            '{"text":"...","mode":"skill|default|stop","route_ids":["draw.clone"],'
            '"bucket":"user","hard":true,"source":"user"}\n',
            encoding="utf-8",
        )
    with dest.open(encoding="utf-8") as fh:
        packaged_n = sum(1 for line in fh if line.strip())
    meta = {
        "packaged_entries": packaged_n,
        "confusion_cards": len(CONFUSION_CARDS),
        "synced_from_packaged": should_copy,
        "note": "Agent 只取 top-k 近邻，禁止整库进上下文",
    }
    (dest_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return dest


def load_bank(root: Path | None = None) -> list[BankEntry]:
    packaged_path = packaged_bank_path()
    entries = load_jsonl(packaged_path)
    if root is not None:
        proj = project_bank_dir(root) / _PACKAGED_NAME
        if proj.is_file():
            # 取较新的一份，避免只 rebuild 打包库却一直读旧项目拷贝
            use_proj = True
            if packaged_path.is_file():
                use_proj = proj.stat().st_mtime >= packaged_path.stat().st_mtime
            if use_proj:
                entries = load_jsonl(proj)
        user_path = user_bank_path(root)
        if user_path.is_file():
            for line in user_path.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                try:
                    raw = json.loads(s)
                except json.JSONDecodeError:
                    continue
                entries.append(
                    BankEntry(
                        text=str(raw.get("text") or ""),
                        mode=str(raw.get("mode") or ""),
                        route_ids=list(raw.get("route_ids") or []),
                        bucket=str(raw.get("bucket") or "user"),
                        reason=str(raw.get("reason") or ""),
                        images=int(raw.get("images") or 0),
                        hard=bool(raw.get("hard", True)),
                        source="user",
                    )
                )
    if not entries:
        # 干净环境缺 jsonl 时现蒸（慢）；正常应带打包库或先 --rebuild
        entries = distill_entries()
    return entries


def retrieve(
    text: str,
    *,
    entries: list[BankEntry] | None = None,
    root: Path | None = None,
    top_k: int = 8,
    expand: bool = True,
) -> list[dict[str, Any]]:
    bank = entries if entries is not None else load_bank(root)
    query_text = expand_colloquial(text) if expand else text
    q = _tokens(query_text)
    scored: list[tuple[float, BankEntry]] = []
    for ent in bank:
        if not ent.text:
            continue
        s = _score(q, _tokens(ent.text))
        if ent.hard:
            s *= 1.08
        if s > 0:
            scored.append((s, ent))
    scored.sort(key=lambda x: (-x[0], 0 if x[1].hard else 1, x[1].text))
    out: list[dict[str, Any]] = []
    for s, ent in scored[: max(1, top_k)]:
        out.append(
            {
                "score": round(s, 4),
                "text": ent.text,
                "mode": ent.mode,
                "route_ids": list(ent.route_ids),
                "bucket": ent.bucket,
                "reason": ent.reason,
                "hard": ent.hard,
                "source": ent.source,
            }
        )
    return out


def _merge_neighbors(*groups: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for group in groups:
        for n in group:
            key = str(n.get("text") or "")
            if not key:
                continue
            prev = best.get(key)
            if prev is None or float(n.get("score") or 0) > float(prev.get("score") or 0):
                best[key] = n
    ranked = sorted(best.values(), key=lambda x: (-float(x.get("score") or 0), x.get("text") or ""))
    return ranked[: max(1, top_k)]


def match_confusion(text: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    raw = text or ""
    for card in CONFUSION_CARDS:
        if re.search(card["keywords"], raw):
            hits.append({"id": card["id"], "when": card["when"], "tip": card["tip"]})
    return hits


def banner_for(plan: Plan) -> str:
    if plan.mode == "stop" or not plan.would_execute:
        if str(plan.reason or "").startswith("artist_ask"):
            return "【路由停】先问你一句"
        return f"【路由停】{plan.reason}"
    if plan.mode == "default" or plan.route_ids == ["draw.ordinary"]:
        return "【走默认路径】按 普通图 走了"
    label = plan.announce.replace("按 ", "").replace(" 走了", "").strip()
    if not label:
        label = "、".join(plan.route_ids) or "未知"
    return f"【按 {label} 走了】"


def confidence_for(plan: Plan, neighbors: list[dict[str, Any]]) -> str:
    if plan.mode == "stop":
        return "ask"  # 停 / 硬不确定：问人或停（与 low 同属「先别执行」）
    if not neighbors:
        return "medium"
    top = neighbors[0]
    agree = False
    if plan.route_ids:
        agree = list(top.get("route_ids") or []) == list(plan.route_ids) or (
            plan.mode == "default" and top.get("mode") == "default"
        )
    score = float(top.get("score") or 0)
    if agree and score >= 0.35:
        return "high"
    if agree or score >= 0.25:
        return "medium"
    return "low"


def advise_route(
    text: str,
    *,
    images: list[str] | None = None,
    image_roles: list[str] | None = None,
    root: Path | None = None,
    top_k: int = 8,
    canonical: str | None = None,
) -> dict[str, Any]:
    """总控入口：口语可先标准化 → 规则分流 + 双路近邻 + 混淆卡。

    - plan 仍以玩家原话为准（回归与关键词规则按原话训的）
    - 标准句（Agent 填写或本地启发式）用于检索增强与交叉校验
    - 原话 plan 与标准句 plan 的 route_ids 冲突 → 降为 low（先别硬执行）
    """
    raw = (text or "").strip()
    pics = list(images or [])
    roles = list(image_roles or [])
    local = build_canonical_brief(raw, images=pics, image_roles=roles)
    agent_canon = (canonical or "").strip()
    # 检索用：优先 Agent 标准句，否则本地启发式（只增强近邻，不单独改判）
    canon_for_retrieve = agent_canon or str(local.get("canonical") or "")
    canon_source = "agent" if agent_canon else "local_heuristic"

    plan = plan_route(raw, images=pics, image_roles=roles)
    plan_canon = (
        plan_route(agent_canon, images=pics, image_roles=roles) if agent_canon else plan
    )
    # 仅 Agent 显式标准句才做双路冲突；本地启发式不准时不误伤置信度
    conflict = False
    if agent_canon:
        if plan.would_execute and plan_canon.would_execute:
            conflict = list(plan.route_ids) != list(plan_canon.route_ids)
        elif plan.mode != plan_canon.mode:
            conflict = True

    neighbors = _merge_neighbors(
        retrieve(raw, root=root, top_k=top_k),
        retrieve(canon_for_retrieve, root=root, top_k=top_k) if canon_for_retrieve else [],
        top_k=top_k,
    )
    confusion = match_confusion(raw + " " + canon_for_retrieve)
    if plan.mode == "default":
        confusion = [c for c in confusion if c.get("id") != "default_ordinary"]

    vague = detect_vague_ask(raw, images=pics, plan=plan)
    artist_ask = ""
    if vague and not conflict:
        artist_ask = str(vague.get("ask") or "")
        # 糊话：改成停，禁止默默普通图
        plan = Plan(
            mode="stop",
            would_execute=False,
            execute=False,
            reason=str(vague.get("reason") or "artist_ask"),
            announce=artist_ask or "先问美术一句",
            serial=False,
            parallel=False,
            route_ids=[],
            steps=[],
        )

    banner = banner_for(plan)
    conf = confidence_for(plan, neighbors)
    if conflict and conf in {"high", "medium"}:
        conf = "low"
    if vague:
        conf = "ask"

    execute_ok = (
        bool(plan.would_execute)
        and not conflict
        and not vague
        and conf in {"high", "medium"}
    )
    detail = artist_detail_for(plan, route_ids=list(plan.route_ids))
    payload = {
        "banner": banner,
        "confidence": conf,
        "plan": plan.to_dict(),
        "plan_canonical": plan_canon.to_dict() if agent_canon else None,
        "canonical": canon_for_retrieve,
        "canonical_source": canon_source,
        "local_canonical": local,
        "plan_conflict": conflict,
        "neighbors": neighbors,
        "confusion": confusion,
        "announce": plan.announce,
        "would_execute": plan.would_execute,
        "execute_ok": execute_ok,
        "mode": plan.mode,
        "route_ids": list(plan.route_ids),
        "top_k": top_k,
        "bank_source": "advise",
        "match_kind": "lexical_ngram+colloquial_expand+canonical",
        "artist_ask": artist_ask,
        "artist_detail": detail if not artist_ask else "先把上面那句回清，我再开始画。",
        "vague_reason": (vague or {}).get("reason") if vague else "",
    }
    payload["artist_say"] = artist_say_for(payload)
    payload["llm_hints"] = {
        "neighbors": [
            {
                "text": n["text"][:80],
                "mode": n["mode"],
                "route_ids": n["route_ids"],
                "score": n["score"],
            }
            for n in neighbors[:5]
        ],
        "confusion": confusion[:4],
        "canonical": canon_for_retrieve[:160],
        "canonical_source": canon_source,
        "plan_conflict": conflict,
        "artist_say": payload["artist_say"],
        "rule": (
            "对美术只贴 artist_say（标签+一句人话），禁止刷 confidence/json。"
            "先写标准路由句再 route --canonical；"
            "execute_ok 才开画；plan_conflict / confidence=ask|low / vague 先问人。"
        ),
    }
    return payload


def format_artist_text(payload: dict[str, Any]) -> str:
    """只给人话：美术零门槛回显。"""
    say = str(payload.get("artist_say") or artist_say_for(payload)).strip()
    return (say + "\n") if say else ""


def format_advise_text(payload: dict[str, Any], *, brief: bool = False) -> str:
    if brief:
        return format_artist_text(payload)
    lines = [
        "── 给美术看（请只转述下面这块）──",
        format_artist_text(payload).rstrip(),
        "── Agent 技术明细 ──",
        payload.get("banner") or "",
        f"confidence: {payload.get('confidence')}  execute_ok: {payload.get('execute_ok')}",
        f"mode: {payload.get('mode')}  would_execute: {payload.get('would_execute')}",
        f"route_ids: {payload.get('route_ids')}",
        f"announce: {payload.get('announce')}",
        f"match: {payload.get('match_kind')}",
    ]
    if payload.get("canonical"):
        lines.append(f"canonical[{payload.get('canonical_source')}]: {payload.get('canonical')}")
    if payload.get("plan_conflict"):
        lines.append("⚠ plan_conflict: 原话规则 vs 标准句规则不一致 → 先问人，勿硬执行")
    if payload.get("vague_reason"):
        lines.append(f"vague: {payload.get('vague_reason')}")
    plan = payload.get("plan") or {}
    if plan.get("reason"):
        lines.append(f"reason: {plan.get('reason')}")
    steps = plan.get("steps") or []
    if steps:
        lines.append("steps:")
        for i, step in enumerate(steps, 1):
            lines.append(
                f"  {i}. {step.get('skill')}/{step.get('section')} → {step.get('deliverable')}"
            )
    neigh = list(payload.get("neighbors") or [])
    top_k = int(payload.get("top_k") or len(neigh) or 8)
    if neigh:
        lines.append(f"top neighbors (k={min(len(neigh), top_k)}, calibrate only):")
        for n in neigh[:top_k]:
            lines.append(
                f"  · {n.get('score')}  {n.get('mode')} {n.get('route_ids')} | {n.get('text')}"
            )
    hints = payload.get("llm_hints") or {}
    confu = list(payload.get("confusion") or hints.get("confusion") or [])
    if confu:
        lines.append("confusion:")
        for c in confu[:4]:
            lines.append(f"  · {c.get('when')} → {c.get('tip')}")
    lines.append(str(hints.get("rule") or ""))
    return "\n".join(lines).rstrip() + "\n"


def append_user_case(root: Path, entry: BankEntry) -> Path:
    """用户自加技能后的话术追加（不静默全收；由调用方显式写入）。"""
    path = user_bank_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry.source = "user"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
    return path
