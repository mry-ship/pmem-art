#!/usr/bin/env python3
"""
pmem-art multi-signal auto-classify + ingest for Cursor-generated / agent-written images.

Signals combined into a confidence score:
  1) path / filename tokens
  2) user or agent prompt text (CN/EN art keywords)
  3) image traits (aspect, alpha, sequence-grid heuristic, UI size, bust vs full-body)
  4) existing modules.yaml path match + style-bible inheritance hints

Low confidence → candidate / misc.* (never silent wrong bucket).
High confidence + auto_add_modules → ensure module exists (extend taxonomy without wiping).
"""
from __future__ import annotations

import fnmatch
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lifecycle import (
    STARTER_CATEGORIES,
    dump_yaml,
    load_candidates_file,
    merge_candidate,
    module_id_from_segments,
    now_iso,
    path_mapped_to_module,
    promote_module,
    sanitize_module_token,
    save_candidates_file,
    write_config_yaml,
    write_modules_yaml,
    guess_category,
)

# --- Keyword lexicons (prompt + path) ---
DOMAIN_LEXICON: dict[str, list[str]] = {
    "brand": [
        "brand", "style", "styleguide", "color script", "colorscript", "palette", "bible",
        "风格", "色板", "色彩圣经", "色彩脚本", "世界观", "logo", "key visual", "kv",
    ],
    "character": [
        "character", "char", "hero", "npc", "avatar", "portrait", "standing", "turnaround",
        "bust", "fullbody", "full-body", "sprite", "立绘", "角色", "人物", "半身", "全身",
        "三视图", "表情", "expression", "face", "头像",
    ],
    "scene": [
        "scene", "environment", "env", "bg", "background", "concept", "keyart", "key art",
        "level", "tile", "prop", "biome", "场景", "原画", "概念图", "气氛图", "地块", "背景",
    ],
    "ui": [
        "ui", "hud", "icon", "button", "panel", "frame", "modal", "nine-slice", "9-slice",
        "9slice", "inventory", "界面", "图标", "弹窗", "九宫格", "按钮", "血条",
    ],
    "vfx": [
        "vfx", "fx", "effect", "slash", "particle", "shader", "impact", "burst",
        "特效", "刀光", "粒子", "受击", "技能特效", "序列帧",
    ],
    "anim": [
        "anim", "animation", "spine", "live2d", "rig", "sequence", "spritesheet", "sprite sheet",
        "帧动画", "骨骼", "序列", "sheet", "walk cycle",
    ],
}

STYLE_LEXICON: dict[str, list[str]] = {
    "Chibi": ["chibi", "q版", "q-version", "sd比例", "头身比小", "可爱变形"],
    "Watercolor": ["watercolor", "水彩", "水墨", "ink wash"],
    "Pixel": ["pixel", "像素", "8bit", "16bit", "dot"],
    "Cyber": ["cyber", "neon", "赛博", "霓虹", "赛博朋克"],
    "Realistic": ["realistic", "写实", "photoreal"],
    "CelShade": ["cel-shade", "celshade", "赛璐珞", "厚涂半赛璐珞", "anime"],
    "Promo": ["promo", "marketing", "宣传", "kv", "key visual", "海报"],
}

ENTITY_STOP = {
    "assets", "art", "arts", "content", "textures", "sprites", "generated", "output",
    "img", "image", "images", "tmp", "temp", "new", "final", "export", "exports",
}


def _score_lexicon(text: str, lexicon: dict[str, list[str]]) -> dict[str, float]:
    t = text.lower()
    scores: dict[str, float] = {}
    for key, words in lexicon.items():
        hit = 0
        for w in words:
            if w.lower() in t:
                hit += 1
        if hit:
            scores[key] = min(1.0, 0.35 + 0.2 * hit)
    return scores


ENTITY_BAD = {
    "立绘", "半身", "全身", "角色", "人物", "表情", "原画", "概念", "概念图", "场景", "背景", "图标",
    "界面", "弹窗", "特效", "刀光", "序列帧", "九宫格", "透明", "水彩", "像素", "气氛图", "底板",
    "portrait", "sprite", "character", "hero", "npc", "icon", "panel", "frame", "sheet",
    "sequence", "slash", "effect", "cute", "fullbody", "bust", "turnaround", "idle",
    "modal", "keyart", "concept", "watercolor", "chibi", "cursor", "generated",
    "vfx", "ui", "fx", "hud", "anim", "brand", "scene", "png", "jpg", "jpeg", "webp",
    "q版", "九宫", "刀光特效", "技能特效",
}

# Tokens that look like entities but are domain/style jargon or agent filename prefixes
ENTITY_DOMAIN_NOISE = {
    "vfx", "ui", "fx", "hud", "npc", "kv", "sd", "rgb", "srgb", "png", "jpg", "jpeg", "webp",
    "cursor", "generated", "gen", "output", "export", "tmp", "temp", "img", "image", "art",
    "lora", "comfy", "comfyui", "midjourney", "mj", "sdxl",
}

FILENAME_PREFIX_STRIP = re.compile(
    r"^(cursor|gen|generated|output|export|tmp|temp|img|image|ai|new)[_\-]+",
    re.I,
)

def _is_bad_entity(tok: str) -> bool:
    if not tok:
        return True
    low = tok.lower()
    if tok in ENTITY_BAD or low in ENTITY_BAD or low in ENTITY_STOP or low in ENTITY_DOMAIN_NOISE:
        return True
    if low in DOMAIN_LEXICON:  # brand/character/scene/ui/vfx/anim keys
        return True
    # ALL-CAPS short acronyms (VFX, UI, FX, HUD…)
    if tok.isupper() and len(tok) <= 4:
        return True
    return False


def _infer_entity_name(path: Path | None, prompt: str) -> str:
    patterns = [
        # Explicit labeled entity
        r"(?:角色|人物|character|hero|npc|立绘角色)[\s:_：\-]*([A-Za-z][A-Za-z0-9_]{1,24}|[\u4e00-\u9fff]{2,12})",
        r"(?:特效|vfx|fx|技能特效)[\s:_：\-]*([A-Za-z][A-Za-z0-9_]{2,24}|[\u4e00-\u9fff]{2,12})",
        r"(?:ui|界面|弹窗|图标|hud)[\s:_：\-]*([A-Za-z][A-Za-z0-9_]{2,24}|[\u4e00-\u9fff]{2,12})",
        r"(?:场景|原画|环境|scene|env)[\s:_：\-]*([A-Za-z][A-Za-z0-9_]{2,24}|[\u4e00-\u9fff]{2,12})",
        r"[「\"']([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9_]{1,16})[」\"']",
        r"(?:name|角色名|姓名|实体)[\s=_：:]+([A-Za-z][A-Za-z0-9_]+|[\u4e00-\u9fff]{2,12})",
    ]
    for pat in patterns:
        m = re.search(pat, prompt, re.I)
        if m and not _is_bad_entity(m.group(1)):
            return sanitize_module_token(m.group(1))

    # Prefer CamelCase / PascalCase with a lowercase letter (FrostSlash, JadeHarbor)
    # over ALLCAPS jargon (VFX, UI)
    camel_hits = []
    for m in re.finditer(r"\b([A-Z][a-zA-Z0-9]{2,24})\b", prompt):
        tok = m.group(1)
        if _is_bad_entity(tok):
            continue
        has_lower = any(c.islower() for c in tok)
        camel_hits.append((0 if has_lower else 1, -len(tok), tok))
    if camel_hits:
        camel_hits.sort()
        return sanitize_module_token(camel_hits[0][2])

    if path:
        stem = path.stem
        stem = FILENAME_PREFIX_STRIP.sub("", stem)
        stem = re.sub(
            r"[_-]?(v\d+|final|draft|rejected|approved|idle|walk|attack|sheet|expr|expression|slash|seq|4f|2x2|9slice|9-slice).*$",
            "",
            stem,
            flags=re.I,
        )
        # also strip trailing art-type tokens
        stem = re.sub(
            r"[_-]?(standing|portrait|modal|keyart|concept|watercolor|chibi|qban|turnaround|bust)$",
            "",
            stem,
            flags=re.I,
        )
        parts = [x for x in re.split(r"[_\-.]+", stem) if x and not _is_bad_entity(x)]
        # Prefer inventory-like substantive tokens over junk
        for cand in parts:
            if cand[:1].isupper() or (cand.islower() and len(cand) >= 3):
                return sanitize_module_token(cand)
        for cand in parts:
            return sanitize_module_token(cand)
        parent = path.parent.name
        if not _is_bad_entity(parent) and parent.lower() not in {
            "generated", "character", "ui", "vfx", "scene", "brand", "anim", "misc", "assets"
        }:
            return sanitize_module_token(parent)
    return "Untitled"

def inspect_image_traits(path: Path) -> dict[str, Any]:
    """Lightweight PNG/JPEG trait probe (reuse pmem_art.inspect_png when available)."""
    traits: dict[str, Any] = {
        "exists": path.is_file(),
        "width": 0,
        "height": 0,
        "has_alpha": False,
        "aspect": 0.0,
        "likely_sequence_sheet": False,
        "likely_ui_icon": False,
        "likely_portrait": False,
        "likely_fullbody": False,
        "likely_keyart": False,
        "frame_guess": 1,
    }
    if not path.is_file():
        return traits
    try:
        from pmem_art import inspect_png
        info = inspect_png(path)
        w, h = int(info.get("width") or 0), int(info.get("height") or 0)
        traits.update({
            "width": w, "height": h,
            "has_alpha": bool(info.get("has_alpha")),
            "mode": info.get("mode"),
            "resolution": info.get("resolution"),
        })
    except Exception:
        # minimal PNG IHDR
        try:
            raw = path.read_bytes()[:33]
            if raw[:8] == b"\x89PNG\r\n\x1a\n":
                import struct
                w, h = struct.unpack(">II", raw[16:24])
                ctype = raw[25]
                traits["width"], traits["height"] = w, h
                traits["has_alpha"] = ctype in (4, 6)
        except Exception:
            return traits
    w, h = traits["width"], traits["height"]
    if w and h:
        traits["aspect"] = round(w / h, 3)
        # sequence sheet: very wide or tall with integer-ish divisions
        if w >= 2 * h and w % h == 0 and w // h in (2, 3, 4, 5, 6, 8):
            traits["likely_sequence_sheet"] = True
            traits["frame_guess"] = w // h
        elif h >= 2 * w and h % w == 0 and h // w in (2, 3, 4, 5, 6, 8):
            traits["likely_sequence_sheet"] = True
            traits["frame_guess"] = h // w
        elif w >= 1024 and h >= 512 and abs((w / h) - 2.0) < 0.15:
            # 1024x512 style sheets
            traits["likely_sequence_sheet"] = True
            traits["frame_guess"] = 4
        # UI icon typical sizes
        if w == h and w in (32, 64, 128, 256, 512) and traits["has_alpha"]:
            traits["likely_ui_icon"] = True
        # portrait / bust (near square) or full-body standing (tall) with alpha
        if traits["has_alpha"] and w >= 256:
            ratio = w / h
            if 0.85 <= ratio <= 1.15:
                traits["likely_portrait"] = True
            elif 0.35 <= ratio <= 0.75 and h >= 512:
                traits["likely_portrait"] = True  # full-body standing treated as character cue
                traits["likely_fullbody"] = True
        # keyart / concept
        if abs((w / h) - 16 / 9) < 0.08 or abs((w / h) - 1.778) < 0.08:
            traits["likely_keyart"] = True
        if w >= 1024 and h >= 576 and not traits["has_alpha"]:
            traits["likely_keyart"] = True
    return traits


def classify_asset(
    root: Path,
    data: dict[str, Any],
    path: str | None = None,
    prompt: str = "",
) -> dict[str, Any]:
    """Return structured classification with confidence and suggested module_id."""
    cfg = (data.get("config") or {}).get("classify") or {}
    modules = data.get("modules") or {}
    w_prompt = float(cfg.get("prompt_weight", 0.35))
    w_path = float(cfg.get("path_weight", 0.25))
    w_img = float(cfg.get("image_trait_weight", 0.25))
    w_mod = float(cfg.get("module_match_weight", 0.15))
    low_t = float(cfg.get("low_confidence_threshold", 0.55))
    high_t = float(cfg.get("high_confidence_threshold", 0.78))
    unknown_domain = cfg.get("unknown_domain", "misc")
    style_parent = cfg.get("style_fork_parent", "brand.WorldStyle")

    path_obj = Path(path) if path else None
    if path_obj and not path_obj.is_absolute():
        path_obj = root / path_obj
    rel = ""
    if path_obj and path_obj.exists():
        try:
            rel = path_obj.relative_to(root).as_posix()
        except ValueError:
            rel = path_obj.name

    path_text = f"{rel} {path_obj.name if path_obj else ''}"
    blob = f"{prompt} {path_text}".strip()

    domain_scores = _score_lexicon(blob, DOMAIN_LEXICON)
    style_scores = _score_lexicon(blob, STYLE_LEXICON)

    traits = inspect_image_traits(path_obj) if path_obj else inspect_image_traits(Path("/nonexistent"))
    # Image trait votes
    img_domain_votes: dict[str, float] = {}
    if traits.get("likely_sequence_sheet"):
        img_domain_votes["vfx"] = img_domain_votes.get("vfx", 0) + 0.55
        img_domain_votes["anim"] = img_domain_votes.get("anim", 0) + 0.45
    if traits.get("likely_ui_icon"):
        img_domain_votes["ui"] = img_domain_votes.get("ui", 0) + 0.7
    if traits.get("likely_portrait") and traits.get("has_alpha"):
        img_domain_votes["character"] = img_domain_votes.get("character", 0) + 0.6
    if traits.get("likely_fullbody") and traits.get("has_alpha"):
        img_domain_votes["character"] = img_domain_votes.get("character", 0) + 0.35
    if traits.get("likely_keyart") and not traits.get("has_alpha"):
        img_domain_votes["scene"] = img_domain_votes.get("scene", 0) + 0.45
        img_domain_votes["brand"] = img_domain_votes.get("brand", 0) + 0.25
    if traits.get("has_alpha") and traits.get("width") == traits.get("height") and traits.get("width") in (256, 512):
        # square alpha can be UI or chibi — only nudge UI if prompt/path already lean UI
        pass
    if traits.get("has_alpha") and traits.get("width") == 512 and traits.get("height") == 512:
        img_domain_votes["ui"] = img_domain_votes.get("ui", 0) + 0.2

    # Existing module path match
    matched = path_mapped_to_module(rel, modules) if rel else None
    match_score = 1.0 if matched else 0.0

    # Combine domain
    combined: dict[str, float] = {}
    for d, s in domain_scores.items():
        combined[d] = combined.get(d, 0) + s * w_prompt
    # path-only lexicon (slightly prefer folder names)
    path_only = _score_lexicon(path_text, DOMAIN_LEXICON)
    for d, s in path_only.items():
        combined[d] = combined.get(d, 0) + s * w_path
    for d, s in img_domain_votes.items():
        combined[d] = combined.get(d, 0) + s * w_img
    if matched:
        cat = modules[matched].get("category") or matched.split(".")[0]
        combined[cat] = combined.get(cat, 0) + match_score * w_mod

    if not combined:
        # last-resort path category guess
        parts = Path(rel).parts if rel else []
        cat = guess_category(list(parts)) if parts else unknown_domain
        combined[cat] = 0.4

    # Priority: explicit character keywords beat 概念图/原画 scene bleed
    prompt_l = prompt.lower()
    char_explicit = any(k in prompt for k in ("角色", "人物", "立绘", "半身", "全身")) or any(
        k in prompt_l for k in ("character", "portrait", "fullbody", "full-body", "chibi", "q版")
    )
    scene_only_cue = any(k in prompt for k in ("场景", "气氛图", "地块", "背景")) or any(
        k in prompt_l for k in ("environment", "keyart", "key art", "biome", "tilemap")
    )
    if char_explicit and not scene_only_cue:
        combined["character"] = combined.get("character", 0) + 0.55
        # 概念图 of a named character is still character (style concept), not scene
        if "scene" in combined and combined["scene"] <= combined.get("character", 0) + 0.2:
            combined["scene"] = max(0.0, combined["scene"] - 0.35)

    domain = max(combined, key=combined.get)
    domain_strength = combined[domain]

    # Style fork detection
    style_fork = None
    if style_scores:
        style_fork = max(style_scores, key=style_scores.get)
    entity = _infer_entity_name(path_obj, prompt)

    if matched and not style_fork:
        suggested = matched
        reason = "path_maps_to_existing_module"
        confidence = min(0.97, 0.7 + domain_strength * 0.2)
    elif matched and style_fork:
        # sibling under style: e.g. character.Astra.Chibi or character.Astra_Watercolor
        base = matched
        # if matched is character.Astra.Expressions keep parent character.Astra
        parts = matched.split(".")
        parent = ".".join(parts[:2]) if len(parts) >= 2 else matched
        suggested = f"{parent}.{style_fork}"
        reason = "style_fork_sibling"
        confidence = min(0.9, 0.55 + style_scores[style_fork] * 0.3 + domain_strength * 0.15)
    else:
        if domain_strength < low_t and not domain_scores and not img_domain_votes:
            domain = unknown_domain
            suggested = f"{unknown_domain}.{entity}"
            reason = "unknown_low_signal"
            confidence = max(0.35, domain_strength)
        else:
            suggested = f"{domain}.{entity}"
            if style_fork and style_scores[style_fork] >= 0.55:
                suggested = f"{domain}.{entity}.{style_fork}"
                reason = "new_module_with_style"
            else:
                reason = "new_module_from_signals"
            confidence = min(0.92, 0.45 + domain_strength)

    # Parent inheritance hint
    parent = None
    if style_fork and domain == "character":
        parent = style_parent if style_parent in modules else None
        # Prefer character base if exists
        base_id = f"character.{entity}"
        if base_id in modules:
            parent = base_id
    if suggested.count(".") >= 2:
        parent_guess = ".".join(suggested.split(".")[:-1])
        if parent_guess in modules:
            parent = parent_guess

    decision = "use_existing"
    if suggested not in modules:
        if confidence >= high_t:
            decision = "auto_add_active"
        elif confidence >= low_t:
            decision = "add_as_candidate"
        else:
            decision = "add_as_misc_candidate"

    signals = {
        "prompt_domain_scores": domain_scores,
        "path_domain_scores": path_only,
        "image_trait_votes": img_domain_votes,
        "style_scores": style_scores,
        "existing_match": matched,
        "weights": {"prompt": w_prompt, "path": w_path, "image": w_img, "module": w_mod},
    }

    result = {
        "ok": True,
        "path": rel or path,
        "prompt": prompt,
        "domain": domain,
        "entity": entity,
        "style_fork": style_fork,
        "suggested_module": suggested,
        "parent": parent,
        "confidence": round(float(confidence), 3),
        "decision": decision,
        "reason": reason,
        "traits": {k: v for k, v in traits.items() if k != "data_uri"},
        "signals": signals,
        "canonical_rel": _canonical_rel(domain, entity, style_fork, path_obj.name if path_obj else "asset.png"),
    }
    return result


def _canonical_rel(domain: str, entity: str, style_fork: str | None, filename: str) -> str:
    ent = entity.lower() if re.fullmatch(r"[A-Za-z0-9_]+", entity) else entity
    if style_fork:
        return f"assets/{domain}/{ent}/{style_fork.lower()}/{filename}"
    return f"assets/{domain}/{ent}/{filename}"


def ensure_module_from_classification(
    root: Path,
    data: dict[str, Any],
    classification: dict[str, Any],
    force_active: bool = False,
) -> tuple[str, str]:
    """
    Extend modules.yaml without wiping. Returns (module_id, status_written).
    """
    modules = data.get("modules") or {}
    categories = data.get("categories") or dict(STARTER_CATEGORIES)
    synonyms = data.get("synonyms")
    cfg = (data.get("config") or {}).get("classify") or {}
    auto_add = bool(cfg.get("auto_add_modules", True))
    mid = classification["suggested_module"]
    domain = classification["domain"]
    decision = classification["decision"]

    if mid in modules:
        # already there — optionally bump scaffold → active on ingest
        if force_active and modules[mid].get("status") != "active":
            modules[mid]["status"] = "active"
            write_modules_yaml(root, categories, modules, synonyms)
            return mid, "active"
        return mid, modules[mid].get("status", "active")

    if not auto_add and not force_active:
        # only queue candidate file
        cands = load_candidates_file(root)
        cands = merge_candidate(
            cands,
            {
                "module_id": mid,
                "category": domain,
                "folder": str(Path(classification.get("canonical_rel", "")).parent),
                "file_count": 1,
                "confidence": classification["confidence"],
                "sample_files": [classification.get("path") or ""],
                "paths_glob": [str(Path(classification.get("canonical_rel", f"assets/{domain}/**")).parent) + "/**"],
                "source": "classify",
            },
        )
        save_candidates_file(root, cands)
        return mid, "candidate_only"

    # Determine status
    if force_active or decision == "auto_add_active":
        status = "active"
    else:
        status = "candidate"

    if domain not in categories:
        if domain in STARTER_CATEGORIES:
            categories[domain] = STARTER_CATEGORIES[domain]
        elif domain == "misc":
            categories["misc"] = {"label": "未归类 / 待提升 (Misc)", "icon": "📦"}
        else:
            categories[domain] = {"label": domain, "icon": "📦"}

    can = classification.get("canonical_rel") or f"assets/{domain}/**"
    folder_glob = str(Path(can).parent).replace("\\", "/") + "/**"

    modules[mid] = {
        "title": f"{classification.get('entity')} ({domain})"
        + (f" · {classification['style_fork']}" if classification.get("style_fork") else ""),
        "category": domain,
        "status": status,
        "description": (
            f"由 classify/ingest 自动扩展 · confidence={classification['confidence']} · "
            f"reason={classification.get('reason')}"
        ),
        "paths": [folder_glob],
        "aliases": [classification.get("entity")],
        "entities": [],
        "palette": [],
        "specs": _default_specs_for_domain(domain, classification.get("traits") or {}, classification.get("style_fork")),
    }
    if classification.get("parent"):
        modules[mid]["parent"] = classification["parent"]

    write_modules_yaml(root, categories, modules, synonyms)
    (root / ".memory-art" / "specs" / mid).mkdir(parents=True, exist_ok=True)

    if status == "candidate":
        cands = load_candidates_file(root)
        cands = merge_candidate(
            cands,
            {
                "module_id": mid,
                "category": domain,
                "folder": str(Path(can).parent),
                "file_count": 1,
                "confidence": classification["confidence"],
                "sample_files": [classification.get("path") or can],
                "paths_glob": [folder_glob],
                "source": "classify_auto_add",
            },
        )
        save_candidates_file(root, cands)

    data["modules"] = modules
    data["categories"] = categories
    return mid, status


def _default_specs_for_domain(domain: str, traits: dict, style_fork: str | None = None) -> dict[str, Any]:
    w, h = traits.get("width") or 0, traits.get("height") or 0
    res = f"{w}x{h}" if w and h else None
    # Concept / promo / watercolor forks are often RGB flats — don't force alpha
    conceptish = (style_fork or "").lower() in {"watercolor", "promo", "realistic", "cyber"}
    if domain == "ui":
        return {
            "resolution": res or "512x512",
            "allowed_resolutions": [res] if res else ["512x512", "256x256", "128x128"],
            "alpha_required": True,
            "nine_slice": [48, 48, 48, 48],
            "safe_margin_px": 4,
            "max_size_kb": 512,
        }
    if domain == "character":
        alpha = True
        if conceptish and not traits.get("has_alpha"):
            alpha = False
        return {
            "resolution": res or "1024x1024",
            "allowed_resolutions": [res] if res else ["1024x1024", "2048x1024"],
            "alpha_required": alpha,
            "safe_margin_px": 16,
            "max_size_kb": 1024,
        }
    if domain in ("vfx", "anim"):
        return {
            "resolution": res or "1024x512",
            "alpha_required": True,
            "safe_margin_px": 16,
            "max_size_kb": 1024,
        }
    if domain == "scene":
        return {"resolution": res or "1024x576", "aspect_ratio": "16:9", "alpha_required": False, "max_size_kb": 2048}
    return {"resolution": res or "1024x1024", "alpha_required": bool(traits.get("has_alpha")), "max_size_kb": 2048}


def seed_asset_record_stub(root: Path, module_id: str, rel_path: str, classification: dict[str, Any]) -> Path:
    entries = root / ".memory-art" / "entries" / module_id
    entries.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    eid = f"INGEST{ts}"
    path = entries / f"{eid}.md"
    from pmem_art import inspect_png
    info = inspect_png(root / rel_path) if (root / rel_path).exists() else {}
    fm = {
        "id": eid,
        "module": module_id,
        "kind": "asset_record",
        "entity": classification.get("entity"),
        "scope": "module",
        "status": "active",
        "author": "pmem-art-ingest",
        "note_date": datetime.now().strftime("%Y-%m-%d"),
        "summary": f"自动入库资产 {rel_path}",
        "assets": [
            {
                "path": rel_path,
                "role": "approved",
                "sha256_16": info.get("sha256_16"),
                "caption": f"ingest conf={classification.get('confidence')} domain={classification.get('domain')}",
            }
        ],
    }
    # simple front matter
    lines = ["---"]
    for k, v in fm.items():
        if k == "assets":
            lines.append("assets:")
            for a in v:
                parts = ", ".join(f"{ik}: {json.dumps(iv, ensure_ascii=False) if isinstance(iv, str) else iv}" for ik, iv in a.items() if iv is not None)
                lines.append(f"  - {{ {parts} }}")
        else:
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False) if isinstance(v, str) else v}")
    lines.append("---")
    lines.append("")
    lines.append(f"由 `pmem_art.py ingest` 自动写入的资产台账桩。")
    lines.append(f"- decision: `{classification.get('decision')}`")
    lines.append(f"- reason: `{classification.get('reason')}`")
    if classification.get("prompt"):
        lines.append(f"- prompt: {classification['prompt'][:500]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def cmd_classify(root: Path, data: dict[str, Any], path: str, prompt: str) -> int:
    result = classify_asset(root, data, path=path or None, prompt=prompt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_ingest(
    root: Path,
    data: dict[str, Any],
    path: str,
    prompt: str = "",
    apply: bool = False,
    seed_record: bool = True,
) -> int:
    """
    classify → ensure module (auto-add) → place into canonical path → optional asset_record stub.
    Default dry-run unless --apply OR config bootstrap.auto_place / classify young auto_place.
    """
    import shutil

    config = data.get("config") or {}
    boot = config.get("bootstrap") or {}
    auto_place = bool(boot.get("auto_place", False))
    do_apply = apply or auto_place

    src = Path(path)
    if not src.is_absolute():
        src = root / src
    if not src.exists():
        print(json.dumps({"ok": False, "error": f"file not found: {path}"}, ensure_ascii=False, indent=2))
        return 1

    classification = classify_asset(root, data, path=str(src), prompt=prompt)
    mid, status = ensure_module_from_classification(
        root, data, classification, force_active=(do_apply and classification["confidence"] >= float((config.get("classify") or {}).get("low_confidence_threshold", 0.55)))
    )
    classification["module_status"] = status
    classification["module_id"] = mid

    dest_rel = classification["canonical_rel"]
    # keep original filename
    dest_rel = str(Path(dest_rel).parent / src.name)
    classification["canonical_rel"] = dest_rel
    dest = root / dest_rel

    plan = {
        "ok": True,
        "action": "ingest",
        "apply": do_apply,
        "classification": classification,
        "place": {
            "from": (src.relative_to(root).as_posix() if str(src.resolve()).startswith(str(root.resolve())) else str(src)),
            "to": dest_rel,
            "will_move": src.resolve() != dest.resolve(),
        },
    }

    if not do_apply:
        plan["message"] = "dry-run：未移动文件、未强制 active。加 --apply 或配置 bootstrap.auto_place: true（年轻项目）后执行。"
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.move(str(src), str(dest))
        plan["place"]["moved"] = True
    else:
        plan["place"]["moved"] = False

    # Promote to active only when confidence clears the low threshold.
    # Low-signal misc stays candidate (file may still be placed under assets/misc/...).
    low_t = float((config.get("classify") or {}).get("low_confidence_threshold", 0.55))
    promote = classification["confidence"] >= low_t
    if promote:
        mid, status = ensure_module_from_classification(
            root,
            data,
            {**classification, "decision": "auto_add_active", "suggested_module": mid},
            force_active=True,
        )
    else:
        # keep candidate; ensure misc category + module already written by first ensure call
        status = (data.get("modules") or {}).get(mid, {}).get("status", "candidate")

    record_path = None
    if seed_record:
        record_path = seed_asset_record_stub(root, mid, dest_rel, classification)
        plan["asset_record"] = str(record_path.relative_to(root))

    plan["module_status"] = status
    plan["message"] = f"已入库 → 模块 {mid} ({status}) · {dest_rel}"
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def cmd_watch_sync_classify(root: Path, data: dict[str, Any], apply: bool = False) -> int:
    """Scan watch_dirs for images not mapped → classify each → queue candidates / optional ingest."""
    cfg = (data.get("config") or {}).get("classify") or {}
    watch = cfg.get("watch_dirs") or ["assets", ".cursor/generated", "generated"]
    from lifecycle import list_image_files, IMAGE_EXTS

    modules = data.get("modules") or {}
    queued = []
    for w in watch:
        base = root / w
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                rel = p.relative_to(root).as_posix()
                if path_mapped_to_module(rel, {k: v for k, v in modules.items() if v.get("status") == "active"}):
                    continue
                queued.append(rel)

    print(f"👀 classify-watch: {len(queued)} unmapped images under {watch}")
    for rel in queued:
        c = classify_asset(root, data, path=rel, prompt="")
        mid, status = ensure_module_from_classification(root, data, c, force_active=False)
        print(f"   · {rel}")
        print(f"     → {c['suggested_module']}  conf={c['confidence']}  decision={c['decision']}  wrote={status}")
        if apply and c["confidence"] >= float(cfg.get("high_confidence_threshold", 0.78)):
            cmd_ingest(root, data, path=rel, prompt="", apply=True, seed_record=True)
    return 0
