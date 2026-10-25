"""Two-layer knowledge atlas and learn CLI."""
from __future__ import annotations

import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .project_library import (
    ensure_project_library_bound,
    slugify_project_id,
    sync_active_project_to_library,
)
from .taste_profile import _mem_root, _uniq_append, load_taste, profile_dir

# ---------------------------------------------------------------------------
# Knowledge atlas — auto-expand breadth
# ---------------------------------------------------------------------------

KNOWLEDGE_DIR = "_knowledge"

DOMAIN_SEED_CARDS: dict[str, list[dict[str, Any]]] = {
    "character": [
        {
            "id": "anatomy-head-ratio",
            "title": "人体结构：头身比尺规与重心控制",
            "tags": ["anatomy", "character", "composition"],
            "body": "写实/二次元立绘标准锁定 7~8 头身（常用 7.5 头身），Q版锁定 2~3 头身；草图阶段必须先标头顶、下巴、胸线、胯部、膝盖五道刻度线并校核重心垂线，严禁头肩比例失调或幼态大头漂移。",
        },
        {
            "id": "eye-hierarchy",
            "title": "人体结构：五官主次与第一识别锚点",
            "tags": ["anatomy", "character"],
            "body": "先定十字中线、眼位与眉弓转折，再定鼻底与唇裂；角色标志性面部特征（如单侧眼镜、异色瞳、机械义眼、面部纹印）必须作为第一识别锚点显式锁定高权重，严禁漏画或左右镜像翻转。",
        },
        {
            "id": "anatomy-hand-five-fingers",
            "title": "人体结构：手部五指解剖与三段透视",
            "tags": ["anatomy", "character"],
            "body": "手部必须先构建掌根方盒截面与拇指球体，再按掌指关节、近节、远节三段圆柱展开五指（1拇指+4指分明），严禁六指畸变、多指粘连或掌骨坍塌。",
        },
    ],
    "scene": [
        {
            "id": "atmospheric-perspective",
            "title": "空间景深：近中远三层大气透视法则",
            "tags": ["scene", "lighting", "composition", "narrative_camera"],
            "body": "场景必须划分近景（高对比暗部压角剪影）、中景（视觉主体与最高明暗对比度）、远景（随空气介质距离递减对比度与饱和度，融入天光雾气），严禁远中近三景饱和度相同导致画面扁平粘连。",
        },
        {
            "id": "golden-hour-scene",
            "title": "光影系统：顶光/侧逆光/黄金时刻与防过曝阴影",
            "tags": ["scene", "lighting", "character"],
            "body": "优先采用 45° 侧逆光（Rim Light 轮廓光分离主体与背景）或黄金时刻低角度暖光配合冷色长影实现冷暖互补；严禁正午垂直顶光造成额头/台阶死白过曝（Overexposure）或暗部死黑脏浊。",
        },
        {
            "id": "composition-thirds-grid",
            "title": "构图法则：九宫格三分法与呼吸留白安全区",
            "tags": ["composition", "scene", "character", "narrative_camera"],
            "body": "将核心视觉焦点布置在九宫格三分线交点（黄金分割点 0.618）上，利用引导线与前景暗角汇聚视线；独立资产四周必须预留 16px~24px 纯透明呼吸安全边距，严禁发冠、武器或特效贴死画布边缘被裁切。",
        },
        {
            "id": "light-rim",
            "title": "光影系统：侧逆光轮廓分离与明暗交界线",
            "tags": ["lighting", "character", "scene"],
            "body": "使用侧逆光（Rim Light）沿角色或主体边缘勾勒高光轮廓线，将主体从深色或复杂背景中干净剥离；明暗交界线保持柔中带刚的体块转折，避免平光导致体积感丧失。",
        },
    ],
    "ui": [
        {
            "id": "nine-slice-basics",
            "title": "UI切图规范：九宫格 48px 包角锁死与纯色拉伸中心",
            "tags": ["ui", "ui_9slice", "composition"],
            "body": "九宫格（9-Slice）组件四角 48x48px 为固定不拉伸包角区（一切雕花装饰必须严格收束在 48px 切线内），四边为单向拉伸区，中央区域必须保持均匀纯色或无方向性平铺底纹以支持 3 倍以上双向拉伸零畸变，严禁在中心拉伸区放置圆盘、斜线或大图案；外周强制保留 4px 纯透明安全边距防止图集溢色（Atlas Bleeding）。",
        },
        {
            "id": "button-state-family",
            "title": "UI交互规范：按钮四态同系家族规范",
            "tags": ["ui", "ui_9slice"],
            "body": "同一交互组件家族必须同步具备 Normal（默认）、Hover（悬停提亮+内发光）、Pressed（按下明度收暗+内凹位移）、Disabled（降饱和灰化降透明度）四态，保持外轮廓、圆角与切线 100% 对齐。",
        },
        {
            "id": "icon-stroke-grid-spec",
            "title": "图标工程规范：线宽统一、安全网格与剪影可读性",
            "tags": ["ui", "icon_consistency", "line_edge"],
            "body": "成套技能/功能图标必须锁定统一的描边线宽（如全局统一 2px 描边，严禁 1px 与 6px 混杂）、统一圆角半径与 16px~24px 安全内边距网格，确保在 64x64px 极小缩略尺寸下主体几何剪影依然一眼可辨、不与背景杂光粘连。",
        },
    ],
    "vfx": [
        {
            "id": "readability-silhouette",
            "title": "剪影可读性与特效预乘 Alpha 通道规范",
            "tags": ["vfx", "line_edge", "icon_consistency"],
            "body": "特效序列帧与图标必须满足黑白剪影第一眼可读性（外轮廓主次分明、具备清晰负空间，主色阶不超过三段：高光亮芯→主色中调→消散外沿）；透明资产必须使用预乘 Alpha（Premultiplied RGBA）彻底消除半透明边缘脏灰黑边，外周内缩 16px 防止序列帧裁切。",
        },
    ],
    "anim": [
        {
            "id": "key-extreme-breakdown",
            "title": "动画运动规律：关键帧-极端帧-中分帧与预备缓冲",
            "tags": ["anim", "character"],
            "body": "动作设计先锁定叙事关键帧（Key）与张力极端帧（Extreme），再插入非对称中分帧（Breakdown）与挤压拉伸（Squash & Stretch），严禁机械平均线性插值导致动作发飘发僵。",
        },
    ],
    "brand": [
        {
            "id": "palette-70-20-10",
            "title": "色彩构成：70-20-10 色板比例黄金法则",
            "tags": ["brand", "color_palette", "character", "scene", "ui"],
            "body": "画面色彩严格遵循 70% 主导底色（稳住大体量与环境基调）、20% 辅助次色（区分结构层级与透气过渡）、10% 高对比点缀色（仅用于视觉中心与核心识别锚点）；严禁未经授权的高饱和荧光/霓虹杂色乱入破坏色调统一。",
        },
        {
            "id": "material-surface-physics",
            "title": "材质表现：金属/织物/陶瓷高光形状与粗糙度区分",
            "tags": ["brand", "material", "character", "ui"],
            "body": "不同材质必须通过高光锐度与菲涅尔反射率严格拉开质感：金属具备高对比硬边高光与环境反光，哑光织物采用宽缓漫反射柔光，釉面/玉石保留温润半透明次表面散射；严禁全图使用同质化油腻塑料感高光。",
        },
    ],
}

ADJACENT_BREADTH: dict[str, list[str]] = {
    "character": ["anatomy", "composition", "lighting", "material", "color_palette"],
    "scene": ["lighting", "composition", "narrative_camera", "brand", "color_palette"],
    "ui": ["ui_9slice", "icon_consistency", "line_edge", "brand", "color_palette", "material"],
    "icon": ["icon_consistency", "ui", "line_edge", "vfx", "color_palette"],
    "vfx": ["line_edge", "anim", "lighting", "color_palette"],
    "anim": ["vfx", "anatomy", "composition"],
    "brand": ["color_palette", "material", "composition"],
    "misc": ["brand", "lighting", "composition"],
}


# Style-specific or project-bound patterns that MUST NOT enter the cross-project shared layer
STYLE_SPECIFIC_PATTERNS: list[str] = [
    r"#[0-9a-fA-F]{3,8}\b",
    r"青瓷|玄青|鎏金|赛博霓虹|霓虹紫|水彩|赛璐珞|厚涂|像素风|watercolor|cel[-\s]?shad|painterly|pixel[-\s]?art",
    r"阿斯特拉|Astra|莱拉|Lyra|云海星穹",
]


def is_style_agnostic_universal_card(card: dict[str, Any]) -> tuple[bool, str]:
    """Verify whether a knowledge card is universally useful and style-agnostic
    (e.g., head-to-body ratio, 70-20-10 color proportion law, atmospheric perspective,
    9-slice structure, silhouette readability) rather than bound to a specific project's
    art style, palette HEX, or character setting.
    """
    cid = str(card.get("id") or "").lower()
    kind = str(card.get("kind") or "").lower()
    tags = [str(t).lower() for t in (card.get("tags") or [])]
    blob = f"{card.get('title') or ''} {card.get('body') or ''}"

    if kind == "style_fork" or cid.startswith("style-") or "style" in tags or "style_lock" in tags:
        return False, "包含特定画风/风格锁定标签 (style / style_lock / style_fork)，仅限项目私有层"
    if cid in ("tech-watercolor", "tech-celshade", "tech-painterly", "tech-pixel"):
        return False, "属于特定渲染画风技法，仅保留在项目私有层以防跨项目串风"
    for pat in STYLE_SPECIFIC_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            return False, f"包含项目专属色值/画风/角色词 ({m.group(0)})，禁止上浮至跨项目共享层"
    return True, "通用无风格绑定美术规律（可跨项目共享）"


def shared_knowledge_dir(root: Path | None = None) -> Path:
    """Global cross-project shared layer directory (~/.pmem-art/shared/ by default,
    or overridden by PMEM_ART_SHARED_DIR environment variable).
    """
    env_dir = os.environ.get("PMEM_ART_SHARED_DIR", "").strip()
    if env_dir:
        d = Path(env_dir).expanduser().resolve()
    else:
        d = (Path.home() / ".pmem-art" / "shared").resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _shared_knowledge_index_path(root: Path | None = None) -> Path:
    return shared_knowledge_dir(root) / "index.json"


def load_shared_knowledge_index(root: Path | None = None, *, auto_seed: bool = True) -> dict[str, Any]:
    p = _shared_knowledge_index_path(root)
    if not p.is_file():
        if auto_seed:
            return ensure_shared_knowledge_seeded(root)
        return {"version": 1, "layer_scope": "shared", "cards": {}, "updated_at": ""}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if auto_seed and not (data.get("cards") or {}):
            return ensure_shared_knowledge_seeded(root)
        return data
    except Exception:
        return {"version": 1, "layer_scope": "shared", "cards": {}, "updated_at": ""}


def save_shared_knowledge_index(idx: dict[str, Any], root: Path | None = None) -> Path:
    idx["layer_scope"] = "shared"
    idx["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    p = _shared_knowledge_index_path(root)
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def upsert_shared_knowledge_card(
    *,
    card_id: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    source: str = "shared_seed",
    promoted_from: str = "",
    root: Path | None = None,
    force: bool = False,
) -> tuple[bool, str, Path | None]:
    candidate = {
        "id": card_id,
        "title": title,
        "body": body,
        "tags": tags or [],
    }
    ok, reason = is_style_agnostic_universal_card(candidate)
    if not ok and not force:
        return False, reason, None

    idx = load_shared_knowledge_index(root, auto_seed=False)
    cards = idx.setdefault("cards", {})
    card = {
        "id": card_id,
        "title": title,
        "body": body,
        "tags": tags or [],
        "source": source,
        "layer_scope": "shared",
        "project_id": "global_shared",
        "project_name": "全局共享通用库 (Global Shared)",
        "universal": True,
        "promoted_from": promoted_from,
        "updated_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
    }
    cards[card_id] = card
    safe = re.sub(r"[^\w\-.]+", "_", card_id)[:80]
    md = shared_knowledge_dir(root) / f"{safe}.md"
    md.write_text(
        f"---\nid: {card_id}\ntitle: {json.dumps(title, ensure_ascii=False)}\n"
        f"layer_scope: shared\nuniversal: true\n"
        f"tags: {json.dumps(tags or [], ensure_ascii=False)}\nsource: {source}\n---\n\n"
        f"# {title}\n\n{body.strip()}\n",
        encoding="utf-8",
    )
    save_shared_knowledge_index(idx, root)
    return True, reason, md


def ensure_shared_knowledge_seeded(root: Path | None = None) -> dict[str, Any]:
    """Ensure the global cross-project shared store (~/.pmem-art/shared/) has the
    universal style-agnostic seed cards (head-to-body ratio, 70-20-10 law, perspective,
    9-slice, silhouette readability, etc.).
    """
    idx = {"version": 1, "layer_scope": "shared", "cards": {}, "updated_at": ""}
    p = _shared_knowledge_index_path(root)
    if p.is_file():
        try:
            idx = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    cards = idx.setdefault("cards", {})
    changed = False
    for dom, card_list in DOMAIN_SEED_CARDS.items():
        for c in card_list:
            cid = c["id"]
            if cid not in cards or cards[cid].get("source") in ("shared_seed", "builtin_universal_seed") or cards[cid].get("body") != c["body"]:
                ok, _ = is_style_agnostic_universal_card(c)
                if ok:
                    cards[cid] = {
                        "id": cid,
                        "title": c["title"],
                        "body": c["body"],
                        "tags": list(c.get("tags") or []),
                        "source": "shared_seed",
                        "layer_scope": "shared",
                        "universal": True,
                        "promoted_from": "builtin_universal_seed",
                        "updated_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
                    }
                    safe = re.sub(r"[^\w\-.]+", "_", cid)[:80]
                    md = shared_knowledge_dir(root) / f"{safe}.md"
                    if not md.exists():
                        md.write_text(
                            f"---\nid: {cid}\ntitle: {json.dumps(c['title'], ensure_ascii=False)}\n"
                            f"layer_scope: shared\nuniversal: true\n"
                            f"tags: {json.dumps(c.get('tags') or [], ensure_ascii=False)}\nsource: shared_seed\n---\n\n"
                            f"# {c['title']}\n\n{c['body'].strip()}\n",
                            encoding="utf-8",
                        )
                    changed = True
    if changed or not p.is_file():
        save_shared_knowledge_index(idx, root)
    return idx


_HAND_FOOT_DEFECT_RE = re.compile(
    r"(手部|手指|五指|六指|多指|断指|手掌|掌骨|手腕|脚部|脚趾|足部|脚踝|鞋带|手脚|解剖缺陷|"
    r"hand\b|finger|thumb|foot\b|feet\b|toe|ankle|shoelace)",
    re.I,
)


def has_hand_or_foot_defect(text: str = "") -> bool:
    """Return True only when hand or foot defects are explicitly detected in query/defects."""
    return bool(_HAND_FOOT_DEFECT_RE.search(str(text or "")))


def recall_layered_knowledge_cards(
    root: Path,
    target_module: str = "",
    query: str = "",
    limit: int = 3,
    defects_hint: str = "",
) -> list[dict[str, Any]]:
    """Recall knowledge cards across BOTH layers (Project-Private .memory-art/_knowledge/
    and Cross-Project Shared ~/.pmem-art/shared/), ranked by `rank_memory_entry`.
    Global anatomy cards in ~/.pmem-art/shared/ are loaded ON-DEMAND ONLY when hand or foot
    defects are explicitly detected in `query` or `defects_hint` (no longer stuffing all 6 cards).
    """
    from .warm_start import rank_memory_entry
    priv_idx = load_knowledge_index(root)
    priv_cards = list((priv_idx.get("cards") or {}).values())
    shared_idx = load_shared_knowledge_index(root, auto_seed=True)
    shared_cards = list((shared_idx.get("cards") or {}).values())

    target_dom = target_module.split(".")[0].lower() if "." in (target_module or "") else (target_module or "").lower()
    domain_adj = set(ADJACENT_BREADTH.get(target_dom, [])) | ({target_dom} if target_dom else set())
    probe_blob = f"{query or ''} {defects_hint or ''}"
    need_hand_foot_anatomy = has_hand_or_foot_defect(probe_blob)
    explicit_head_ratio = "头身比" in probe_blob

    candidates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    # 1. Project-private cards first (tagged layer_scope='private')
    for c in priv_cards:
        c_copy = dict(c)
        c_copy["layer_scope"] = "private"
        cid = str(c_copy.get("id") or "")
        if cid:
            seen_ids.add(cid)
        candidates.append(c_copy)

    # 2. Cross-project shared cards (tagged layer_scope='shared', skipped if overridden privately)
    #    Global anatomy cards are mounted ON-DEMAND ONLY when hand/foot defects are detected!
    for c in shared_cards:
        cid = str(c.get("id") or "")
        if cid in seen_ids:
            continue
        tags = {str(t).lower() for t in (c.get("tags") or [])}
        is_anatomy_card = ("anatomy" in tags) or cid.startswith("anatomy-") or (cid == "eye-hierarchy")
        if is_anatomy_card:
            if not need_hand_foot_anatomy:
                continue
            if cid != "anatomy-hand-five-fingers" and not (cid == "anatomy-head-ratio" and explicit_head_ratio):
                continue
        if cid in ("golden-hour-scene", "light-rim") and not any(k in probe_blob for k in ("夕阳", "逆光", "轮廓光", "黄金时刻", "光影")):
            continue
        if cid in ("material-surface-physics", "key-extreme-breakdown") and not any(k in probe_blob for k in ("材质", "金属", "动画", "关键帧")):
            continue
        c_copy = dict(c)
        c_copy["layer_scope"] = "shared"
        candidates.append(c_copy)

    # Filter to cards relevant to target_module/domain or query when module is specified
    filtered: list[dict[str, Any]] = []
    for c in candidates:
        tags = {str(t).lower() for t in (c.get("tags") or [])}
        if not target_dom or (tags & domain_adj) or ("brand" in tags) or ("color_palette" in tags):
            filtered.append(c)
        elif query and rank_memory_entry(c, target_module=target_module, query=query)[4] > 0:
            filtered.append(c)

    filtered.sort(
        key=lambda c: rank_memory_entry(c, target_module=target_module, query=query),
        reverse=True,
    )
    return filtered[:limit]


def promote_card_to_shared(
    root: Path,
    card_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Promote a project-private knowledge card to the cross-project shared layer
    if it is style-agnostic and universally applicable.
    """
    priv_idx = load_knowledge_index(root)
    priv_cards = priv_idx.get("cards") or {}
    if card_id not in priv_cards:
        return {"ok": False, "id": card_id, "reason": f"项目私有知识库中不存在卡片 {card_id}"}
    card = priv_cards[card_id]
    ok, reason, md_path = upsert_shared_knowledge_card(
        card_id=card["id"],
        title=card.get("title") or card["id"],
        body=card.get("body") or "",
        tags=list(card.get("tags") or []),
        source="promoted_from_project",
        promoted_from=root.name,
        root=root,
        force=force,
    )
    if ok:
        card["promoted_to_shared"] = True
        save_knowledge_index(root, priv_idx)
    return {
        "ok": ok,
        "id": card_id,
        "title": card.get("title"),
        "reason": reason,
        "shared_path": str(md_path) if md_path else "",
    }


def knowledge_dir(root: Path) -> Path:
    d = _mem_root(root) / KNOWLEDGE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _knowledge_index_path(root: Path) -> Path:
    return knowledge_dir(root) / "index.json"


def load_knowledge_index(root: Path) -> dict[str, Any]:
    meta = ensure_project_library_bound(root)
    pid = meta.get("project_id") or slugify_project_id(root.name)
    pname = meta.get("project_name") or root.name
    p = _knowledge_index_path(root)
    if not p.is_file():
        return {"version": 1, "layer_scope": "private", "project_id": pid, "project_name": pname, "cards": {}, "updated_at": ""}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data["layer_scope"] = "private"
        data["project_id"] = pid
        data["project_name"] = pname
        for c in (data.get("cards") or {}).values():
            if isinstance(c, dict):
                c["layer_scope"] = "private"
                c["project_id"] = pid
                c["project_name"] = pname
        return data
    except Exception:
        return {"version": 1, "layer_scope": "private", "project_id": pid, "project_name": pname, "cards": {}, "updated_at": ""}


def save_knowledge_index(root: Path, idx: dict[str, Any]) -> Path:
    meta = ensure_project_library_bound(root)
    pid = meta.get("project_id") or slugify_project_id(root.name)
    pname = meta.get("project_name") or root.name
    idx["layer_scope"] = "private"
    idx["project_id"] = pid
    idx["project_name"] = pname
    idx["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    p = _knowledge_index_path(root)
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_active_project_to_library(root)
    return p


def upsert_knowledge_card(
    root: Path,
    *,
    card_id: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    source: str = "auto",
    promote_if_universal: bool = True,
) -> Path:
    meta = ensure_project_library_bound(root)
    pid = meta.get("project_id") or slugify_project_id(root.name)
    pname = meta.get("project_name") or root.name
    idx = load_knowledge_index(root)
    cards = idx.setdefault("cards", {})
    candidate = {"id": card_id, "title": title, "body": body, "tags": tags or []}
    is_univ, _ = is_style_agnostic_universal_card(candidate)
    card = {
        "id": card_id,
        "title": title,
        "body": body,
        "tags": tags or [],
        "source": source,
        "layer_scope": "private",
        "project_id": pid,
        "project_name": pname,
        "universal": is_univ,
        "promoted_to_shared": False,
        "updated_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
    }
    if promote_if_universal and is_univ:
        ok, _, _ = upsert_shared_knowledge_card(
            card_id=card_id,
            title=title,
            body=body,
            tags=tags or [],
            source=f"auto_promoted:{source}",
            promoted_from=root.name,
            root=root,
        )
        card["promoted_to_shared"] = ok

    cards[card_id] = card
    # also write individual markdown for human browsing
    safe = re.sub(r"[^\w\-.]+", "_", card_id)[:80]
    md = knowledge_dir(root) / f"{safe}.md"
    md.write_text(
        f"---\nid: {card_id}\ntitle: {json.dumps(title, ensure_ascii=False)}\n"
        f"layer_scope: private\nuniversal: {str(is_univ).lower()}\n"
        f"tags: {json.dumps(tags or [], ensure_ascii=False)}\nsource: {source}\n---\n\n"
        f"# {title}\n\n{body.strip()}\n",
        encoding="utf-8",
    )
    save_knowledge_index(root, idx)
    return md


def ingest_term_to_knowledge(root: Path, text: str, *, source: str = "feedback") -> list[str]:
    """When feedback/ref-analysis introduces technique/style terms, grow atlas."""
    created: list[str] = []
    term_map = [
        (r"水彩|watercolor", "tech-watercolor", "水彩渲染", ["style", "material"], "边缘扩散、纸本纹理、低饱和层染；避免厚涂油腻高光。"),
        (r"赛璐珞|cel[\s-]?shad", "tech-celshade", "赛璐珞分层", ["style", "material"], "硬边色块分层，高光形状干净，层数克制。"),
        (r"厚涂|painterly|oil", "tech-painterly", "厚涂笔触", ["style", "material"], "可见笔触方向跟随形体，暗部透气勿脏。"),
        (r"像素|pixel", "tech-pixel", "像素艺术", ["style"], "锁调色板与像素网格，禁止糊边抗锯齿乱入。"),
        (r"九宫格|9[- ]?slice", "tech-9slice", "九宫格切图", ["ui"], "四角固定、中心可拉伸；中心禁止复杂装饰。"),
        (r"侧逆光|rim\s*light", "light-rim", "侧逆光", ["lighting"], "轮廓分离主体与背景，高光条沿边缘走。"),
        (r"黄金时刻|golden\s*hour", "light-golden-hour", "黄金时刻光", ["lighting", "scene"], "低角度暖光与长影，适合 Key Art。"),
        (r"大气透视|atmospheric", "scene-atm-persp", "大气透视", ["scene"], "远景降对比，近景保边缘。"),
        (r"Q版|chibi", "style-chibi", "Q版头身", ["character", "style"], "2~3 头身，五官放大但识别锚点保留。"),
        (r"电影感|cinematic", "cam-cinematic", "电影感镜头", ["narrative_camera"], "景深、侧逆光、叙事构图优先于装饰细节。"),
        (r"currentColor|stroke-width|viewBox", "icon-svg-spec", "SVG 图标规格", ["icon_consistency", "ui"], "统一 viewBox / stroke / currentColor，视觉重量一致。"),
    ]
    for pat, cid, title, tags, body in term_map:
        if re.search(pat, text or "", re.I):
            idx = load_knowledge_index(root)
            if cid not in (idx.get("cards") or {}):
                upsert_knowledge_card(root, card_id=cid, title=title, body=body, tags=tags, source=source, promote_if_universal=False)
                created.append(cid)
            else:
                # refresh touch
                upsert_knowledge_card(root, card_id=cid, title=title, body=body, tags=tags, source=source, promote_if_universal=False)
                created.append(cid)
    return list(dict.fromkeys(created))


def propose_breadth_expansions(
    root: Path,
    data: dict[str, Any],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Suggest 3–5 breadth expansions based on active domains vs gaps."""
    modules = data.get("modules") or {}
    active_domains: set[str] = set()
    for mid, cfg in modules.items():
        if (cfg or {}).get("status", "active") != "active":
            continue
        active_domains.add(mid.split(".")[0] if "." in mid else mid)

    idx = load_knowledge_index(root)
    have = set((idx.get("cards") or {}).keys())
    proposals: list[dict[str, Any]] = []

    # Seed cards missing for active domains
    for dom in sorted(active_domains):
        for card in DOMAIN_SEED_CARDS.get(dom, []):
            if card["id"] not in have:
                proposals.append({
                    "kind": "knowledge_card",
                    "id": card["id"],
                    "title": card["title"],
                    "tags": card.get("tags") or [],
                    "body": card.get("body") or "",
                    "reason": f"你已有 {dom} 域模块，但知识库缺少「{card['title']}」",
                    "optional_module_stub": "",
                })

    # Adjacent domain gaps
    for dom in sorted(active_domains):
        for adj in ADJACENT_BREADTH.get(dom, []):
            # adj may be category not domain
            if adj in DOMAIN_SEED_CARDS and adj not in active_domains:
                for card in DOMAIN_SEED_CARDS[adj][:1]:
                    if card["id"] not in have:
                        proposals.append({
                            "kind": "adjacent_domain",
                            "id": card["id"],
                            "title": card["title"],
                            "tags": card.get("tags") or [],
                            "body": card.get("body") or "",
                            "reason": f"从 {dom} 扩展到相邻域 {adj}：补「{card['title']}」",
                            "optional_module_stub": f"{adj}.General",
                        })
            # category-level knowledge
            if adj in DRILLS and f"cap-{adj}" not in have:
                proposals.append({
                    "kind": "capability_card",
                    "id": f"cap-{adj}",
                    "title": f"能力卡：{adj}",
                    "tags": [adj, "capability"],
                    "body": DRILLS[adj][0],
                    "reason": f"短板/相邻能力「{adj}」尚无知识卡",
                    "optional_module_stub": "",
                })

    # Style fork suggestions from taste banned/preferred
    taste = load_taste(root)
    if taste.get("banned_habits") and "style-anti-neon" not in have:
        proposals.append({
            "kind": "style_fork",
            "id": "style-anti-neon",
            "title": "反霓虹风格约束",
            "tags": ["style_lock", "brand"],
            "body": "禁用霓虹紫与廉价赛博高光；主色走青瓷白/墨蓝/鎏金或项目色板。",
            "reason": "口味档案含霓虹/赛博类禁用 → 固化为风格知识卡",
            "optional_module_stub": "",
        })

    # de-dupe by id
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    for p in proposals:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        uniq.append(p)
        if len(uniq) >= limit:
            break
    return uniq


def accept_breadth_proposals(
    root: Path,
    data: dict[str, Any],
    proposals: list[dict[str, Any]],
    *,
    seed_modules: bool = False,
) -> dict[str, Any]:
    written: list[str] = []
    stubs: list[str] = []
    for p in proposals:
        path = upsert_knowledge_card(
            root,
            card_id=p["id"],
            title=p["title"],
            body=p.get("body") or p.get("reason") or "",
            tags=list(p.get("tags") or []),
            source="learn_accept",
        )
        written.append(str(path.relative_to(root)))
        stub = p.get("optional_module_stub") or ""
        if seed_modules and stub:
            # write empty scaffold entry note only — do not mutate modules.yaml aggressively
            mod_dir = _mem_root(root) / "entries" / stub
            mod_dir.mkdir(parents=True, exist_ok=True)
            note = mod_dir / "LEARN_SEED.md"
            if not note.exists():
                note.write_text(
                    f"---\nid: LEARNSEED\nmodule: {stub}\nkind: art_plan\nstatus: active\n"
                    f"summary: \"知识广度扩展种子模块\"\n---\n\n"
                    f"由 `/pmem-learn` 接受建议创建的空种子。可用 `accept` / `ingest` 正式激活。\n"
                    f"关联知识卡: {p['id']} — {p['title']}\n",
                    encoding="utf-8",
                )
                stubs.append(stub)
    return {"written": written, "module_stubs": stubs}


def cmd_learn(
    root: Path,
    data: dict[str, Any],
    action: str = "suggest",
    *,
    limit: int = 5,
    accept_all: bool = False,
    seed_modules: bool = False,
    ids: list[str] | None = None,
    silent: bool = False,
) -> int:
    if action in ("suggest", "propose", ""):
        props = propose_breadth_expansions(root, data, limit=limit)
        stash = profile_dir(root) / "learn_proposals.json"
        stash.write_text(json.dumps({"proposals": props, "at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"), "silent": silent}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if silent:
            return 0
        print("🌍 `/pmem-learn` 知识广度扩展建议（进阶 peek）\n")
        if not props:
            print("   · 暂无新建议（知识库已较完整，或模块仍空）。日常已在 finish 后静默 enqueue。")
            return 0
        for i, p in enumerate(props, 1):
            print(f"   {i}. [{p.get('kind')}] {p.get('title')}  ({p.get('id')})")
            print(f"      原因: {p.get('reason')}")
            if p.get("optional_module_stub"):
                print(f"      可选模块种子: {p['optional_module_stub']}")
        print(f"\n   · 建议已暂存: .memory-art/_profile/learn_proposals.json")
        print("   · 接受全部: python3 pmem_art.py learn accept --all")
        print("   · 接受指定: python3 pmem_art.py learn accept --ids id1,id2")
        if accept_all:
            return cmd_learn(root, data, "accept", accept_all=True, seed_modules=seed_modules, limit=limit, silent=False)
        return 0

    if action == "accept":
        stash = profile_dir(root) / "learn_proposals.json"
        props: list[dict[str, Any]] = []
        if stash.is_file():
            try:
                props = (json.loads(stash.read_text(encoding="utf-8")).get("proposals")) or []
            except Exception:
                props = []
        if not props:
            props = propose_breadth_expansions(root, data, limit=limit)
        if ids:
            idset = set(ids)
            props = [p for p in props if p.get("id") in idset]
        elif not accept_all:
            print("❌ 请指定 --all 或 --ids id1,id2")
            return 1
        result = accept_breadth_proposals(root, data, props, seed_modules=seed_modules)
        print("✅ 已写入知识卡:")
        for w in result["written"]:
            print(f"   · {w}")
        if result["module_stubs"]:
            print("🌱 模块种子:")
            for s in result["module_stubs"]:
                print(f"   · {s}")
        return 0

    if action == "list":
        idx = load_knowledge_index(root)
        priv_cards = idx.get("cards") or {}
        s_idx = load_shared_knowledge_index(root, auto_seed=True)
        shared_cards = s_idx.get("cards") or {}
        print(f"📚 双层知识广度图谱（项目私有 {len(priv_cards)} 张 + 跨项目全局共享 {len(shared_cards)} 张）\n")
        print(f"🔒 [Layer 1 · 项目私有层] .memory-art/_knowledge/ ({len(priv_cards)} 张):")
        if not priv_cards:
            print("   （当前项目私有层为空）")
        for cid, c in sorted(priv_cards.items()):
            prom = " 🌐[已同步共享层]" if c.get("promoted_to_shared") else " 🔒[仅本项目]"
            print(f"   · {cid}: {c.get('title')}  tags={c.get('tags')}{prom}")
        print(f"\n🌐 [Layer 2 · 跨项目共享层] {shared_knowledge_dir(root)} ({len(shared_cards)} 张 · 纯通用无风格绑定):")
        for cid, c in sorted(shared_cards.items()):
            print(f"   · {cid}: {c.get('title')}  tags={c.get('tags')}  (from={c.get('promoted_from') or 'seed'})")
        return 0

    if action == "promote":
        priv_idx = load_knowledge_index(root)
        priv_cards = priv_idx.get("cards") or {}
        target_ids = ids if ids else (list(priv_cards.keys()) if accept_all else [])
        if not target_ids:
            print("❌ 请指定 --ids card1,card2 或 --all 将项目私有通用知识卡上浮至跨项目共享层")
            return 1
        promoted, blocked = [], []
        for cid in target_ids:
            res = promote_card_to_shared(root, cid, force=False)
            if res.get("ok"):
                promoted.append(res)
            else:
                blocked.append(res)
        if promoted:
            print(f"🌐 已上浮至跨项目共享层 ({shared_knowledge_dir(root)}):")
            for r in promoted:
                print(f"   ✅ {r['id']} ({r.get('title')}) — {r.get('reason')}")
        if blocked:
            print("🔒 以下卡片因含项目特定画风/色板被拦截在项目私有层（防止跨项目污染）:")
            for r in blocked:
                print(f"   🛡️ {r['id']} ({r.get('title', '')}) — {r.get('reason')}")
        return 0

    print(f"未知 learn 子操作: {action}（suggest|accept|list|promote）")
    return 1
