#!/usr/bin/env python3
"""
pmem-art lifecycle: Mode A (young / cold start), Mode B (legacy onboard), Mode C (continuous sync).
Guarantees a mountable memory workflow that is never fully blind magic — auto-propose + one confirmation.
"""
from __future__ import annotations

import fnmatch
import json
import re
import shutil
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MEMORY_DIR = ".memory-art"
# Maximum module hierarchy / inherits chain depth (PMEM-aligned 4-layer hard cap)
MAX_MODULE_DEPTH = 4
MAX_INHERITS_DEPTH = 4
MAX_SEGMENT_SUBDEPTH = MAX_MODULE_DEPTH - 1  # category (L1) + up to 3 sub-segments = 4 layers


def _warn_depth_cap(msg: str) -> None:
    import sys as _sys
    print(f"⚠️ [pmem-art] {msg}", file=_sys.stderr)


def is_junk_sidecar_name(name: str) -> bool:
    """True for macOS AppleDouble (`._*`), Finder junk, and Office lock files."""
    n = (name or "").strip()
    if not n:
        return True
    if n.startswith("._"):
        return True
    if n in (".DS_Store", "Thumbs.db", "desktop.ini"):
        return True
    if n.startswith("~$"):
        return True
    return False


def iter_md_files(directory: Path, *, recursive: bool = True):
    """Yield ``*.md`` under directory, skipping AppleDouble / junk sidecars."""
    if not directory.is_dir():
        return
    it = directory.rglob("*.md") if recursive else directory.glob("*.md")
    for p in sorted(it):
        if is_junk_sidecar_name(p.name):
            continue
        yield p


def get_module_parent(mod_cfg: dict[str, Any] | None) -> str | None:
    """Return explicit parent/inherits target from module config (supports both `inherits` and `parent`)."""
    if not isinstance(mod_cfg, dict):
        return None
    inh = mod_cfg.get("inherits")
    if isinstance(inh, list) and inh:
        inh = inh[0]
    val = inh or mod_cfg.get("parent")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def clamp_module_id_depth(
    module_id: str,
    max_depth: int = MAX_MODULE_DEPTH,
    *,
    warn: bool = True,
) -> tuple[str, bool]:
    """Clamp dot-separated module ID to at most `max_depth` segments (e.g. L1.L2.L3.L4)."""
    mid = (module_id or "").strip(".")
    if not mid:
        return "misc.Untitled", False
    parts = [p for p in mid.split(".") if p]
    if len(parts) <= max_depth:
        return ".".join(parts), False
    clamped = ".".join(parts[:max_depth])
    if warn:
        _warn_depth_cap(
            f"模块层级深度超过 {max_depth} 层硬顶限制: '{module_id}' ({len(parts)} 层) → 已自动截断至 '{clamped}' ({max_depth} 层)"
        )
    return clamped, True


def resolve_module_lineage(
    module_id: str,
    modules: dict[str, Any] | None,
    max_depth: int = MAX_INHERITS_DEPTH,
    *,
    warn: bool = False,
) -> list[str]:
    """
    Resolve module inheritance chain [self, parent1, parent2, ...] capped at `max_depth` (4 layers).
    Supports both `inherits` and `parent` fields plus dot-prefix parent fallback, with cycle protection.
    """
    if not module_id:
        return []
    mods = modules or {}
    chain: list[str] = []
    seen: set[str] = set()
    curr: str | None = module_id
    while curr and curr not in seen:
        if len(chain) >= max_depth:
            if warn:
                _warn_depth_cap(
                    f"模块 '{module_id}' 的 inherits/parent 继承链超过 {max_depth} 层硬顶限制 → 已在 '{chain[-1]}' 处截断 ({' -> '.join(chain)})"
                )
            break
        chain.append(curr)
        seen.add(curr)
        cfg = mods.get(curr) if isinstance(mods.get(curr), dict) else {}
        nxt = get_module_parent(cfg)
        if not nxt and "." in curr:
            prefix = ".".join(curr.split(".")[:-1])
            if prefix in mods:
                nxt = prefix
        if nxt and nxt in seen:
            if warn:
                _warn_depth_cap(f"检测到模块继承环路: {' -> '.join(chain)} -> {nxt}，已自动断开")
            break
        curr = nxt
    return chain


def clamp_inherits_parent(
    module_id: str,
    proposed_parent: str | None,
    modules: dict[str, Any] | None,
    max_depth: int = MAX_INHERITS_DEPTH,
    *,
    warn: bool = True,
) -> tuple[str | None, bool]:
    """
    Ensure setting `module_id -> proposed_parent` does not create an inheritance chain > `max_depth` (4 layers).
    If `proposed_parent` already has a chain of >= max_depth, shifts the parent pointer up so total depth <= 4.
    """
    if not proposed_parent:
        return None, False
    parent_clamped, _ = clamp_module_id_depth(proposed_parent, max_depth=max_depth, warn=warn)
    if parent_clamped == module_id:
        return None, True
    mods = modules or {}
    # Walk ancestors starting from parent_clamped
    ancestors: list[str] = []
    seen: set[str] = {module_id}
    curr: str | None = parent_clamped
    while curr and curr not in seen and len(ancestors) < max_depth + 4:
        ancestors.append(curr)
        seen.add(curr)
        cfg = mods.get(curr) if isinstance(mods.get(curr), dict) else {}
        nxt = get_module_parent(cfg)
        if not nxt and "." in curr:
            prefix = ".".join(curr.split(".")[:-1])
            if prefix in mods and prefix != curr:
                nxt = prefix
        curr = nxt
    # Total chain is [module_id] + ancestors. Max allowed ancestors is max_depth - 1 (3 ancestors + self = 4 layers).
    max_ancestors = max(1, max_depth - 1)
    if len(ancestors) <= max_ancestors:
        return parent_clamped, (parent_clamped != proposed_parent)
    # Shift parent to the highest ancestor suffixes so [module_id] + tail has length == max_depth
    effective_parent = ancestors[-(max_ancestors)]
    if warn:
        full_chain = " -> ".join([module_id] + ancestors)
        _warn_depth_cap(
            f"模块 '{module_id}' 的 inherits 继承链 ({full_chain}) 超过 {max_depth} 层硬顶限制 → 已自动截断并绑定至第 {max_depth - 1} 层父模块 '{effective_parent}'"
        )
    return effective_parent, True

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tga", ".psd", ".gif", ".exr", ".tif", ".tiff"}
IGNORE_DIR_NAMES = {
    ".git", ".svn", ".perforce", ".memory-art", ".cursor", "__pycache__",
    "node_modules", "Library", "Temp", "obj", "bin", ".idea", ".vscode",
}

# Starter taxonomy: inactive scaffolds after `init` / `bootstrap --mode young`
STARTER_CATEGORIES = {
    "brand": {"label": "全局风格圣经 (Brand & Style Bible)", "icon": "🎨"},
    "character": {"label": "角色与立绘绑定 (Character & Rigging)", "icon": "🧝‍♀️"},
    "scene": {"label": "场景与地块物件 (Scene & Environment)", "icon": "🏯"},
    "ui": {"label": "界面与九宫格图标 (UI & 9-Slice HUD)", "icon": "💠"},
    "vfx": {"label": "特效与序列帧表现 (VFX & Shaders)", "icon": "✨"},
    "anim": {"label": "骨骼动画与 Live2D/Spine (Animation)", "icon": "🦴"},
}

STARTER_MODULES: dict[str, dict[str, Any]] = {
    "brand.WorldStyle": {
        "title": "全局世界观色彩圣经（脚手架）",
        "category": "brand",
        "status": "scaffold",
        "description": "冷启动脚手架：放入色板、色彩脚本、Negative Prompt 总表后，用 accept 或写入第一条 art_decision 自动提升为 active。",
        "paths": ["assets/brand/**"],
        "aliases": ["StyleGuide", "ColorBible", "色彩圣经"],
        "entities": ["ColorRatio", "GlobalNegative"],
        "palette": [],
        "specs": {"resolution": "1024x576", "aspect_ratio": "16:9", "alpha_required": False, "max_size_kb": 2048},
    },
    "character.Hero": {
        "title": "主角立绘（脚手架 · 请改名为实际角色）",
        "category": "character",
        "status": "scaffold",
        "description": "冷启动脚手架：将主角立绘/三视图放入 assets/character/<Name>/ 后，sync 会提出 character.<Name> 候选。",
        "paths": ["assets/character/**"],
        "aliases": ["Hero", "主角"],
        "entities": ["Proportions", "Turnaround"],
        "palette": [],
        "specs": {"resolution": "1024x1024", "aspect_ratio": "1:1", "alpha_required": True, "safe_margin_px": 16, "max_size_kb": 1024},
    },
    "scene.MainArea": {
        "title": "主场景（脚手架）",
        "category": "scene",
        "status": "scaffold",
        "description": "冷启动脚手架：放入概念图 / Tilemap / Props 后提升为 active。",
        "paths": ["assets/scene/**"],
        "aliases": ["MainArea", "主场景"],
        "entities": ["KeyArt", "Lighting"],
        "palette": [],
        "specs": {"resolution": "1024x576", "aspect_ratio": "16:9", "alpha_required": False, "max_size_kb": 2048},
    },
    "ui.HUD": {
        "title": "主界面 HUD / 弹窗（脚手架）",
        "category": "ui",
        "status": "scaffold",
        "description": "冷启动脚手架：九宫格底板、图标、字体规范放入 assets/ui/。",
        "paths": ["assets/ui/**"],
        "aliases": ["HUD", "UI", "九宫格"],
        "entities": ["NineSlice", "Icon"],
        "palette": [],
        "specs": {
            "resolution": "512x512",
            "aspect_ratio": "1:1",
            "alpha_required": True,
            "nine_slice": [48, 48, 48, 48],
            "safe_margin_px": 4,
            "max_size_kb": 512,
        },
    },
    "vfx.Combat": {
        "title": "战斗特效（脚手架）",
        "category": "vfx",
        "status": "scaffold",
        "description": "冷启动脚手架：序列帧 / Shader 参数约束放入 assets/vfx/。",
        "paths": ["assets/vfx/**"],
        "aliases": ["CombatVFX", "特效"],
        "entities": ["SpriteSheet", "PremultipliedAlpha"],
        "palette": [],
        "specs": {"resolution": "1024x512", "alpha_required": True, "safe_margin_px": 16, "max_size_kb": 1024},
    },
    "anim.Spine": {
        "title": "Spine / Live2D 绑定（脚手架）",
        "category": "anim",
        "status": "scaffold",
        "description": "冷启动脚手架：骨骼图层命名规范、导出目录放入 assets/anim/。",
        "paths": ["assets/anim/**"],
        "aliases": ["Spine", "Live2D", "骨骼"],
        "entities": ["LayerNaming", "Export"],
        "palette": [],
        "specs": {"alpha_required": True, "max_size_kb": 2048},
    },
}

COMMON_LEGACY_ROOTS = [
    "assets", "Art", "art", "Arts", "Content", "content",
    "Resources/Art", "Assets/Art", "Assets/Arts", "GameArt",
    "Textures", "Sprites", "UI", "Characters", "Environments", "VFX",
]

CATEGORY_KEYWORDS = {
    "brand": ["brand", "style", "styleguide", "color", "palette", "bible", "风格", "色板", "色彩", "logo"],
    "character": ["character", "characters", "char", "chars", "hero", "npc", "avatar", "portrait", "spine", "live2d", "角色", "立绘", "人物"],
    "scene": ["scene", "env", "environment", "level", "map", "bg", "background", "tile", "prop", "场景", "地图", "地块"],
    "ui": ["ui", "hud", "icon", "button", "panel", "frame", "font", "界面", "图标", "弹窗"],
    "vfx": ["vfx", "fx", "effect", "particle", "shader", "slash", "特效", "粒子", "刀光"],
    "anim": ["anim", "animation", "rig", "motion", "timeline", "动画", "骨骼"],
    "misc": ["misc", "other", "unsorted", "inbox", "dump", "scratch", "未归类"],
}

# Folder-name synonyms stripped when building module ids (Art/Characters/Astra → character.Astra)
CATEGORY_SEGMENT_ALIASES: dict[str, set[str]] = {
    "brand": {"brand", "style", "styleguide", "styles", "bible", "风格", "色板"},
    "character": {"character", "characters", "char", "chars", "heroes", "npc", "npcs", "avatar", "avatars", "角色", "立绘", "人物"},
    "scene": {"scene", "scenes", "env", "environment", "environments", "level", "levels", "bg", "background", "场景", "地图"},
    "ui": {"ui", "hud", "gui", "ux", "interface", "界面", "图标"},
    "vfx": {"vfx", "fx", "effect", "effects", "特效", "粒子"},
    "anim": {"anim", "animation", "animations", "rig", "rigs", "动画", "骨骼"},
    "misc": {"misc", "other", "unsorted", "inbox", "dump", "scratch", "未归类"},
}


def dump_yaml(data: Any, indent: int = 0) -> str:
    """Minimal YAML emitter for dict/list/scalar (no anchors). Enough for modules.yaml / config.yaml."""
    sp = "  " * indent
    if isinstance(data, dict):
        if not data:
            return "{}"
        lines: list[str] = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                if not v:
                    lines.append(f"{sp}{k}: " + ("[]" if isinstance(v, list) else "{}"))
                else:
                    lines.append(f"{sp}{k}:")
                    nested = dump_yaml(v, indent + 1)
                    lines.append(nested if nested.endswith("\n") else nested + "\n")
            else:
                lines.append(f"{sp}{k}: {_yaml_scalar(v)}")
        out = "\n".join(x.rstrip("\n") for x in lines)
        return out + ("\n" if indent == 0 else "")
    if isinstance(data, list):
        if not data:
            return "[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                # Prefer inline for small flat dicts (palette rows)
                if item and all(not isinstance(x, (dict, list)) for x in item.values()) and len(item) <= 6:
                    parts = ", ".join(f"{ik}: {_yaml_scalar(iv)}" for ik, iv in item.items())
                    lines.append(f"{sp}- {{ {parts} }}")
                else:
                    first = True
                    for ik, iv in item.items():
                        prefix = "- " if first else "  "
                        first = False
                        if isinstance(iv, (dict, list)) and iv:
                            lines.append(f"{sp}{prefix}{ik}:")
                            lines.append(dump_yaml(iv, indent + 2).rstrip("\n"))
                        else:
                            lines.append(f"{sp}{prefix}{ik}: {_yaml_scalar(iv)}")
            elif isinstance(item, list):
                lines.append(f"{sp}-")
                lines.append(dump_yaml(item, indent + 1).rstrip("\n"))
            else:
                lines.append(f"{sp}- {_yaml_scalar(item)}")
        return "\n".join(lines) + ("\n" if indent == 0 else "")
    return _yaml_scalar(data)


def _yaml_scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "":
        return '""'
    if any(c in s for c in ":#{}[]&*!|>%@`'\"\n") or s.strip() != s or s.lower() in ("true", "false", "null", "yes", "no"):
        return json.dumps(s, ensure_ascii=False)
    return s


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def default_config(project_name: str = "Untitled Art Project", mode: str = "young") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "project": {
            "name": project_name,
            "art_style": "",
            "color_space": "sRGB",
            "engine": "",
            "lifecycle_mode": mode,  # young | legacy | mature
        },
        "vcs": "auto",
        "gate": {
            "mode": "warn" if mode == "young" else "block",
            "auto_validate_on_save": True,
            "stale_check": {"hash": True, "dimensions": True, "alpha": True, "png_metadata": True},
            "skip_markers": ["跳过美术记忆", "skip-art-memory"],
        },
        "write": {
            "default_status": "active",
            "require_visual_anchor": True,
            "max_per_day_per_entity": 10,
            "auto_promote_candidate_on_record": True,
        },
        "bootstrap": {
            "asset_roots": ["assets"],
            "auto_accept_depth": 2,
            "candidate_min_files": 1,
            "never_auto_move": True,
            "scaffold_dirs": True,
            "confirmed": False,
            "last_sync_at": None,
            "auto_place": mode == "young",
        },
        "classify": {
            "auto_add_modules": True,
            "max_module_depth": MAX_MODULE_DEPTH,
            "max_inherits_depth": MAX_INHERITS_DEPTH,
            "low_confidence_threshold": 0.55,
            "high_confidence_threshold": 0.78,
            "unknown_domain": "misc",
            "style_fork_parent": "brand.WorldStyle",
            "watch_dirs": ["assets", ".cursor/generated", "generated"],
            "prompt_weight": 0.35,
            "path_weight": 0.25,
            "image_trait_weight": 0.25,
            "module_match_weight": 0.15,
        },
        "converge": {
            "merged_generate_and_judge": False,
            "stop_policy": "dynamic_threshold",
            "default_scale": "medium",
            "max_rounds": 8,
            "target_thresholds": {
                "low": 9.6,
                "medium": 9.6,
                "high": 9.6,
                "recompose": 9.6,
            },
        },
        "vlm_judge": {
            "enabled": "auto",
            "provider": "openai",
            "api_key": "",
            "api_key_env": "PMEM_VLM_API_KEY",
            "base_url": "",
            "model": "",
            "timeout_sec": 90,
            "on_error": "fallback",
            "write_sidecar": True,
        },
    }


def write_modules_yaml(root: Path, categories: dict, modules: dict, synonyms: list | None = None) -> Path:
    mem = root / MEMORY_DIR
    mem.mkdir(parents=True, exist_ok=True)
    # Enforce 4-layer hard cap on module IDs and inherits/parent chains
    clamped_modules: dict[str, Any] = {}
    for raw_mid, mcfg in (modules or {}).items():
        mid, _ = clamp_module_id_depth(str(raw_mid), max_depth=MAX_MODULE_DEPTH, warn=True)
        cfg_copy = dict(mcfg) if isinstance(mcfg, dict) else {}
        raw_parent = get_module_parent(cfg_copy)
        if raw_parent:
            safe_parent, _ = clamp_inherits_parent(mid, raw_parent, modules, max_depth=MAX_INHERITS_DEPTH, warn=True)
            if safe_parent:
                cfg_copy["parent"] = safe_parent
                if "inherits" in cfg_copy:
                    cfg_copy["inherits"] = safe_parent
            else:
                cfg_copy.pop("parent", None)
                cfg_copy.pop("inherits", None)
        clamped_modules[mid] = cfg_copy
    modules = clamped_modules
    doc = {
        "schema_version": 1,
        "categories": categories,
        "synonyms": synonyms
        or [
            ["立绘", "半身像", "全身像", "portrait", "sprite"],
            ["九宫格", "9-slice", "拉伸框", "弹窗底板"],
            ["去背", "透明通道", "alpha", "抠图", "白边"],
            ["废案", "红线", "打回", "redline", "don't"],
            ["配方", "工作流", "lora", "prompt", "comfyui", "seed"],
        ],
        "modules": modules,
    }
    path = mem / "modules.yaml"
    header = (
        "# pmem-art modules.yaml — status: scaffold | candidate | active\n"
        "# scaffold = 冷启动空壳（引导落盘路径）; candidate = sync 自动提议（待 accept）; active = 已确认生效\n"
    )
    path.write_text(header + dump_yaml(doc), encoding="utf-8")
    return path


def write_config_yaml(root: Path, config: dict) -> Path:
    mem = root / MEMORY_DIR
    mem.mkdir(parents=True, exist_ok=True)
    path = mem / "config.yaml"
    header = "# pmem-art config.yaml — 挂载式美术记忆生命周期配置\n"
    path.write_text(header + dump_yaml(config), encoding="utf-8")
    return path


def ensure_cursor_stubs(root: Path) -> None:
    """写入/刷新 Cursor 对话驱动的规则、hooks 以及自动安装 Cursor / Claude Code / Codex 技能（Skills & Commands）。"""
    rules = root / ".cursor" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    mdc = rules / "pmem-art.mdc"
    mdc.write_text(
        "---\n"
        "description: pmem-art — Cursor 对话驱动的个人美术积累记忆与 /pmem-draw 闭环收敛生图规则\n"
        "globs:\n  - assets/**\n  - Art/**\n  - .memory-art/**\n  - .cursor/generated/**\n"
        "alwaysApply: true\n"
        "---\n\n"
        "# pmem-art：个人美术积累记忆 & 内置生图技能\n\n"
        "## 1. 内置斜杠技能（用户输入即触发）\n"
        "- **`/pmem-draw`（或 `/art-draw`）**：8轮 9.6分 闭环自评收敛生图！\n"
        "  - 纯文本：`/pmem-draw 生成一张xxx风格的xxx图`\n"
        "  - 垫图模式：`/pmem-draw [丢入一张图] 生成一张xxx图`（先深度分析参考图构图/色板/光影/结构，再开始循环）\n"
        "  - 循环规则：每轮先 `converge generate` 生 1 张，再 `converge judge` 做严苛五维审图（满分10）+ 说出合理亮点与**不合理之处**，并在对话展示评分/不足/改点 → `< 9.6` 分不算合格，叠加修正策略继续下一轮（最多8轮）→ 达标立即停止，或满8轮挑全阶段最高分 → 运行 `python3 pmem_art.py converge finish`（默认写记忆并打印评分履历；只要终稿加 `--quiet`）。\n"
        "- **`/pmem-ui`（`/art-ui`）**：**【强制8轮≥9.6】** SpriteCook 式 UI Kit/HUD/九宫格整套（概念先行→组件表→9-slice→状态族）。\n"
        "- **`/pmem-concept`（`/art-concept`）**：**【强制8轮≥9.6】** 原画/概念图/Key Art（ZHO·FLUX 完整句）— 与 draw 同等闭环，禁止只生一张。\n"
        "- **`/pmem-icon`（`/art-icon`）**：**【强制8轮≥9.6】** jezweb 式一致化图标集/SVG（style-spec→分批→preview；关键枚闭环）。\n"
        "- **`/pmem-style-lock`（`/art-style`）**：从参考样张提炼风格圣经与色板锁定。\n"
        "- **`/pmem-critique`（`/art-check`）**：单图/批量图主美级五维审稿挑刺并写入红线。\n"
        "- **`/pmem-variant`（`/art-variant`）**：同角色跨画风分叉（Q版/水彩/像素）或表情动作差分。\n"
        "- **`/pmem-atlas`（`/art-map`）**：归档散图并刷新 `art-atlas.html`。\n\n"
        "## 2. 日常生图前必查与对话反馈沉淀\n"
        "- 生图前：`python3 pmem_art.py search --module <模块>` 或 `search <关键词>`，把历史红线/定稿写进约束。\n"
        "- 用户说「太赛博/头太大/别这样画/这版留着/换成水彩/以后都用…」时立刻：\n"
        "  `python3 pmem_art.py feedback \"<原话>\" --module <模块> [--asset <图>]`\n"
        "- 新图可 `ingest <路径> -p \"...\" --apply`；用户说「跳过美术记忆」时可跳过。\n",
        encoding="utf-8",
    )
    hooks = root / ".cursor" / "hooks.json"
    hooks.write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "preToolUse": [
                        {
                            "command": "python3 pmem_art.py hook pre-gen",
                            "matcher": "GenerateImage|Write|Edit|StrReplace|MCP",
                            "failClosed": False,
                        }
                    ],
                    "postToolUse": [
                        {
                            "command": "python3 pmem_art.py hook post-asset",
                            "matcher": "GenerateImage|Write|Edit",
                        }
                    ],
                    "stop": [{"command": "python3 pmem_art.py hook stop", "loop_limit": 1}],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        from skills_kit import install_skills_and_agent_configs
        install_skills_and_agent_configs(root, quiet=True)
    except Exception as exc:
        print(f"⚠️ 安装技能包时出现警告: {exc}")



def sanitize_module_token(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^\w\u4e00-\u9fff.-]+", "", name, flags=re.UNICODE)
    name = name.replace("-", "_")
    if not name:
        return "Untitled"
    # Prefer PascalCase for Latin tokens
    if re.fullmatch(r"[A-Za-z0-9_]+", name):
        parts = re.split(r"[_\s]+", name)
        return "".join(p[:1].upper() + p[1:] for p in parts if p)
    return name


def guess_category(path_parts: list[str]) -> str:
    joined = "/".join(p.lower() for p in path_parts)
    # Prefer exact path-segment hits over substring (avoids "char" inside unrelated words)
    lowered = [p.lower() for p in path_parts]
    for cat, keys in CATEGORY_KEYWORDS.items():
        keyset = {k.lower() for k in keys} | {cat}
        for seg in lowered:
            if seg in keyset:
                return cat
    for cat, keys in CATEGORY_KEYWORDS.items():
        for k in keys:
            # whole-path substring only for multi-char CN / longer EN keys
            if len(k) >= 3 and k.lower() in joined:
                return cat
    if path_parts:
        first = path_parts[0].lower()
        for cat, keys in CATEGORY_KEYWORDS.items():
            if first in {k.lower() for k in keys} or first == cat:
                return cat
    return "misc"


def module_id_from_segments(category: str, segments: list[str], depth: int) -> str:
    """Build module id like character.Astra or character.Astra.Expressions from path segments (hard-capped at 4 layers)."""
    capped_subdepth = min(max(1, depth), MAX_SEGMENT_SUBDEPTH)
    if depth > MAX_SEGMENT_SUBDEPTH:
        _warn_depth_cap(
            f"目录扫描深度 depth={depth} 超过模块 4 层硬顶限制（category + 最多 {MAX_SEGMENT_SUBDEPTH} 层子路径）→ 已自动截断至 {MAX_MODULE_DEPTH} 层"
        )
    raw = [s for s in segments if s]
    aliases = CATEGORY_SEGMENT_ALIASES.get(category, set()) | {category}
    # Drop leading segments that are just the domain folder (Characters, UI, vfx…)
    while raw and raw[0].lower() in {a.lower() for a in aliases}:
        raw = raw[1:]
    if len(raw) > capped_subdepth:
        if len(raw) > MAX_SEGMENT_SUBDEPTH:
            _warn_depth_cap(
                f"路径分段 {category}.{'.'.join(sanitize_module_token(s) for s in raw)} 超过 {MAX_MODULE_DEPTH} 层硬顶限制 → 已截断至前 {MAX_MODULE_DEPTH} 层"
            )
        raw = raw[:capped_subdepth]
    segs = [sanitize_module_token(s) for s in raw if s]
    if not segs:
        segs = ["Main"]
    mid, _ = clamp_module_id_depth(category + "." + ".".join(segs), max_depth=MAX_MODULE_DEPTH, warn=True)
    return mid


def list_image_files(root: Path, asset_roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for r in asset_roots:
        base = root / r
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if is_junk_sidecar_name(p.name) or any(is_junk_sidecar_name(part) for part in p.parts):
                continue
            if any(part in IGNORE_DIR_NAMES for part in p.parts):
                continue
            if p.suffix.lower() in IMAGE_EXTS:
                files.append(p)
    return files


def path_mapped_to_module(rel: str, modules: dict[str, Any]) -> str | None:
    for mid, cfg in modules.items():
        for pat in cfg.get("paths") or []:
            if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.replace("**/", "")):
                return mid
        # also direct folder match
        for pat in cfg.get("paths") or []:
            folder = pat.split("*")[0].rstrip("/")
            if folder and (rel == folder or rel.startswith(folder + "/")):
                return mid
    return None


def discover_folder_clusters(root: Path, asset_roots: list[str], depth: int = 2) -> list[dict[str, Any]]:
    """Cluster images by parent folders up to `depth` under each asset root."""
    heat: dict[str, dict[str, Any]] = {}
    for img in list_image_files(root, asset_roots):
        try:
            rel = img.relative_to(root).as_posix()
        except ValueError:
            continue
        parts = Path(rel).parts
        # drop filename
        dir_parts = list(parts[:-1])
        if not dir_parts:
            continue
        # find which asset root
        root_name = dir_parts[0]
        under = dir_parts[1:]
        use_depth = min(depth, len(under)) if under else 0
        key_parts = [root_name] + under[:use_depth] if use_depth else [root_name]
        key = "/".join(key_parts)
        bucket = heat.setdefault(
            key,
            {"folder": key, "files": [], "count": 0, "exts": set(), "sample": []},
        )
        bucket["count"] += 1
        bucket["files"].append(rel)
        bucket["exts"].add(img.suffix.lower())
        if len(bucket["sample"]) < 5:
            bucket["sample"].append(rel)
    out = []
    for folder, info in sorted(heat.items(), key=lambda x: -x[1]["count"]):
        parts = folder.split("/")
        under = parts[1:]
        cat = guess_category(parts)
        mid = module_id_from_segments(cat, under if under else [parts[-1]], depth=max(1, len(under) or 1))
        conf = 0.55
        if any(k in folder.lower() for keys in CATEGORY_KEYWORDS.values() for k in keys):
            conf += 0.2
        if info["count"] >= 3:
            conf += 0.1
        if info["count"] >= 10:
            conf += 0.1
        conf = min(0.95, conf)
        out.append(
            {
                "folder": folder,
                "module_id": mid,
                "category": cat,
                "file_count": info["count"],
                "confidence": round(conf, 2),
                "sample_files": info["sample"],
                "paths_glob": [folder + "/**"],
            }
        )
    return out


def cmd_init(root: Path, project_name: str = "Untitled Art Project", force: bool = False) -> int:
    mem = root / MEMORY_DIR
    explicit_name = project_name if (project_name and project_name != "Untitled Art Project") else ""
    eff_name = explicit_name or root.name
    was_copied = False
    if mem.exists():
        try:
            from improve import ensure_project_library_bound, sync_active_project_to_library
            meta = ensure_project_library_bound(root, explicit_project_name=explicit_name)
            was_copied = bool(meta.get("auto_isolated_on_copy"))
            if explicit_name:
                cfg_now = default_config(explicit_name, mode="young")
                write_config_yaml(root, cfg_now)
                sync_active_project_to_library(root, project_name=explicit_name)
        except Exception:
            pass
    if mem.exists() and not force and not was_copied:
        print(f"⚠️  已存在 {mem}。若要重建脚手架请加 --force（不会删除已有 entries）。")
        print("   年轻项目下一步: python3 pmem_art.py bootstrap --mode young")
        print("   老项目下一步:   python3 pmem_art.py bootstrap --mode legacy")
        return 0

    config = default_config(eff_name, mode="young")
    write_config_yaml(root, config)

    modules = {k: dict(v) for k, v in STARTER_MODULES.items()}
    write_modules_yaml(root, STARTER_CATEGORIES, modules)

    (mem / "entries").mkdir(parents=True, exist_ok=True)
    (mem / "specs").mkdir(parents=True, exist_ok=True)
    (mem / "_knowledge").mkdir(parents=True, exist_ok=True)
    if not (mem / "_knowledge" / "index.json").exists():
        (mem / "_knowledge" / "index.json").write_text(
            json.dumps({"version": 1, "layer_scope": "private", "cards": {}, "updated_at": ""}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    (mem / "candidates.json").write_text("[]\n", encoding="utf-8")
    try:
        from improve import ensure_shared_knowledge_seeded, ensure_project_library_bound, sync_active_project_to_library
        ensure_shared_knowledge_seeded(root)
        ensure_project_library_bound(root, explicit_project_name=eff_name)
        sync_active_project_to_library(root, project_name=eff_name)
    except Exception:
        pass

    # Scaffold empty asset dirs matching taxonomy
    for cat in STARTER_CATEGORIES:
        d = root / "assets" / cat
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    ensure_cursor_stubs(root)

    guide = mem / "ONBOARDING.md"
    guide.write_text(
        "# pmem-art 冷启动指南（Mode A · Young）\n\n"
        "1. `init` 已放入 **scaffold（脚手架）** 模块与 `assets/{brand,character,scene,ui,vfx,anim}/` 空目录。\n"
        "2. 把第一批图拖进对应目录（或任意子文件夹）。\n"
        "3. 运行 `python3 pmem_art.py sync` → 系统提出 **candidate** 模块（带置信度）。\n"
        "4. `python3 pmem_art.py candidates` 查看；`accept <module_id>` 确认提升为 **active**。\n"
        "5. 可选：`bootstrap --mode young --auto-accept-depth 2` 自动接受前 1–2 层路径为模块。\n"
        "6. 用 `place <文件> --module character.Hero --apply` 把散落文件归位到规范路径。\n"
        "7. 闸门默认 `gate.mode=warn`，直到 `bootstrap` 确认后可改为 `block`。\n"
        "8. 写完记忆或新资产后：`atlas` 刷新可视化图谱。\n",
        encoding="utf-8",
    )

    print("✅ pmem-art init 完成（Mode A · 冷启动脚手架）")
    print(f"   · {MEMORY_DIR}/config.yaml  (gate.mode=warn, lifecycle_mode=young)")
    print(f"   · {MEMORY_DIR}/modules.yaml (6 个 scaffold 模块)")
    print("   · assets/{brand,character,scene,ui,vfx,anim}/ 空目录已创建")
    print("   · .cursor/rules/pmem-art.mdc + hooks.json")
    print("   · 已自动注入 8 大技能 (/pmem-draw, /pmem-ui, /pmem-concept, /pmem-icon, /pmem-style-lock, /pmem-critique, /pmem-variant, /pmem-atlas) 到 .cursor / .claude / .agents")
    print(f"   · {MEMORY_DIR}/ONBOARDING.md")
    print("\n保证工作流（非盲目魔法）：")
    print("   落盘 → sync 提议 candidate → accept 一次确认 → search 闸门生效 → record/validate → atlas")
    print("\n下一步: python3 pmem_art.py bootstrap --mode young")
    return 0


def load_candidates_file(root: Path) -> list[dict[str, Any]]:
    p = root / MEMORY_DIR / "candidates.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_candidates_file(root: Path, items: list[dict[str, Any]]) -> None:
    p = root / MEMORY_DIR / "candidates.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def merge_candidate(existing: list[dict], item: dict) -> list[dict]:
    by_id = {c["module_id"]: c for c in existing}
    mid = item["module_id"]
    if mid in by_id:
        old = by_id[mid]
        old["file_count"] = max(old.get("file_count", 0), item.get("file_count", 0))
        old["confidence"] = max(old.get("confidence", 0), item.get("confidence", 0))
        samples = list(dict.fromkeys((old.get("sample_files") or []) + (item.get("sample_files") or [])))[:8]
        old["sample_files"] = samples
        old["folder"] = item.get("folder", old.get("folder"))
        old["updated_at"] = now_iso()
    else:
        item = dict(item)
        item["created_at"] = now_iso()
        item["status"] = "candidate"
        by_id[mid] = item
    return list(by_id.values())


def promote_module(
    root: Path,
    modules: dict[str, Any],
    categories: dict[str, Any],
    module_id: str,
    proposal: dict[str, Any] | None = None,
    synonyms: list | None = None,
) -> dict[str, Any]:
    """Promote scaffold/candidate → active; create if missing from proposal (enforces 4-layer hard cap)."""
    module_id, _ = clamp_module_id_depth(module_id, max_depth=MAX_MODULE_DEPTH, warn=True)
    if module_id in modules:
        modules[module_id]["status"] = "active"
        if proposal:
            modules[module_id]["paths"] = proposal.get("paths_glob") or modules[module_id].get("paths") or []
            modules[module_id]["title"] = modules[module_id].get("title") or module_id
    else:
        cat = (proposal or {}).get("category") or module_id.split(".")[0]
        modules[module_id] = {
            "title": module_id.split(".")[-1],
            "category": cat,
            "status": "active",
            "description": f"由 sync/bootstrap 提升确认 · 源文件夹 {(proposal or {}).get('folder', '')}",
            "paths": (proposal or {}).get("paths_glob") or [f"assets/{cat}/**"],
            "aliases": [module_id.split(".")[-1]],
            "entities": [],
            "palette": [],
            "specs": {},
        }
        if cat not in categories and cat in STARTER_CATEGORIES:
            categories[cat] = STARTER_CATEGORIES[cat]
        elif cat not in categories:
            categories[cat] = {"label": cat, "icon": "📦"}
    write_modules_yaml(root, categories, modules, synonyms)
    # ensure specs dir
    (root / MEMORY_DIR / "specs" / module_id).mkdir(parents=True, exist_ok=True)
    return modules[module_id]


def cmd_sync(root: Path, data: dict[str, Any], auto_accept_depth: int | None = None, apply_accept: bool = False) -> int:
    config = data.get("config") or {}
    boot = config.get("bootstrap") or {}
    roots = boot.get("asset_roots") or ["assets"]
    depth = auto_accept_depth if auto_accept_depth is not None else int(boot.get("auto_accept_depth", 2))
    min_files = int(boot.get("candidate_min_files", 1))

    modules = data.get("modules") or {}
    categories = data.get("categories") or dict(STARTER_CATEGORIES)
    synonyms = data.get("synonyms")

    clusters = discover_folder_clusters(root, roots, depth=max(depth, 2))
    candidates = load_candidates_file(root)
    new_proposals = []
    auto_accepted = []
    orphans = []

    for c in clusters:
        if c["file_count"] < min_files:
            continue
        mapped = None
        # if any file already maps to an active module, skip proposing duplicate
        for sample in c["sample_files"]:
            mapped = path_mapped_to_module(sample, {k: v for k, v in modules.items() if v.get("status", "active") == "active"})
            if mapped:
                break
        if mapped:
            continue
        # depth-based auto accept policy
        folder_parts = c["folder"].split("/")
        under_depth = max(0, len(folder_parts) - 1)
        if apply_accept and under_depth <= depth and c["confidence"] >= 0.55:
            promote_module(root, modules, categories, c["module_id"], c, synonyms)
            # reload modules reference
            auto_accepted.append(c)
            c["status"] = "active"
            c["auto_accepted"] = True
        else:
            candidates = merge_candidate(candidates, c)
            new_proposals.append(c)

    # orphan files: under roots but not matching any active/candidate/scaffold path
    all_mods = modules
    for img in list_image_files(root, roots):
        rel = img.relative_to(root).as_posix()
        if not path_mapped_to_module(rel, all_mods):
            orphans.append(rel)

    save_candidates_file(root, candidates)
    boot["last_sync_at"] = now_iso()
    config["bootstrap"] = boot
    write_config_yaml(root, config)
    # rewrite modules if auto-accepted
    if auto_accepted:
        write_modules_yaml(root, categories, modules, synonyms)

    print(f"🔄 sync 完成 · 扫描根目录: {roots} · auto_accept_depth={depth}")
    print(f"   新/更新候选模块: {len(new_proposals)}  |  自动提升(active): {len(auto_accepted)}  |  未映射孤儿文件: {len(orphans)}")
    for c in new_proposals[:20]:
        print(f"   • [candidate conf={c['confidence']}] {c['module_id']:<32} ← {c['folder']} ({c['file_count']} files)")
    for c in auto_accepted[:20]:
        print(f"   • [auto-active conf={c['confidence']}] {c['module_id']:<32} ← {c['folder']}")
    if orphans[:10]:
        print("   孤儿样本（可用 place 归位）:")
        for o in orphans[:10]:
            print(f"      - {o}")
    if len(orphans) > 10:
        print(f"      … 另有 {len(orphans) - 10} 个")
    print("\n下一步: python3 pmem_art.py candidates")
    print("       python3 pmem_art.py accept <module_id>")
    print("       python3 pmem_art.py place <file> --module <id> --apply")
    return 0


def cmd_candidates(root: Path) -> int:
    items = load_candidates_file(root)
    pending = [c for c in items if c.get("status", "candidate") == "candidate"]
    print(f"📋 待确认候选模块: {len(pending)}\n")
    if not pending:
        print("   （空）运行 sync 或 bootstrap --mode legacy 以扫描资产树。")
        return 0
    print(f"{'模块 ID':<36} {'置信度':<8} {'文件数':<8} {'源文件夹'}")
    print("-" * 90)
    for c in sorted(pending, key=lambda x: -x.get("confidence", 0)):
        print(f"{c['module_id']:<36} {c.get('confidence', 0):<8} {c.get('file_count', 0):<8} {c.get('folder', '')}")
        for s in (c.get("sample_files") or [])[:3]:
            print(f"   ↳ {s}")
    print("\n确认: python3 pmem_art.py accept <module_id>")
    print("全部: python3 pmem_art.py accept --all")
    return 0


def cmd_accept(root: Path, data: dict[str, Any], module_id: str, accept_all: bool = False) -> int:
    candidates = load_candidates_file(root)
    modules = data.get("modules") or {}
    categories = data.get("categories") or dict(STARTER_CATEGORIES)
    synonyms = data.get("synonyms")

    targets: list[dict[str, Any]] = []
    if accept_all:
        # Only candidates.json entries — never silent-promote empty/broad scaffold shells
        # (scaffold paths like assets/character/** would otherwise swallow every character file).
        # Promote a scaffold explicitly: accept character.Hero
        targets = [c for c in candidates if c.get("status", "candidate") == "candidate"]
    elif module_id:
        # find in candidates or modules scaffolds
        found = next((c for c in candidates if c["module_id"] == module_id), None)
        if found:
            targets = [found]
        elif module_id in modules:
            targets = [{"module_id": module_id, "paths_glob": modules[module_id].get("paths"), "category": modules[module_id].get("category"), "folder": ""}]
        else:
            print(f"❌ 未找到候选或脚手架模块: {module_id}")
            return 1
    else:
        print("请指定 module_id 或使用 --all")
        return 1

    accepted = []
    for t in targets:
        mid = t["module_id"]
        promote_module(root, modules, categories, mid, t, synonyms)
        for c in candidates:
            if c["module_id"] == mid:
                c["status"] = "accepted"
                c["accepted_at"] = now_iso()
        accepted.append(mid)
        print(f"✅ 已提升为 active: {mid}")

    save_candidates_file(root, candidates)
    if accepted:
        config = data.get("config") or {}
        boot = config.setdefault("bootstrap", {})
        boot["confirmed"] = True
        boot["last_sync_at"] = boot.get("last_sync_at") or now_iso()
        config["bootstrap"] = boot
        # Keep gate=warn for legacy until user opts into block; young may already be block
        write_config_yaml(root, config)
    print(f"\n共确认 {len(accepted)} 个模块。闸门 search 现可按模块召回记忆。")
    return 0


def cmd_place(
    root: Path,
    data: dict[str, Any],
    src: str,
    module: str = "",
    role: str = "approved",
    apply: bool = False,
    plan_all_orphans: bool = False,
) -> int:
    """Move/copy a file into the module's canonical assets path. Default is dry-run plan."""
    modules = data.get("modules") or {}
    boot = (data.get("config") or {}).get("bootstrap") or {}
    plans: list[dict[str, str]] = []

    def infer_module_for(rel: str) -> str | None:
        if module:
            return module
        m = path_mapped_to_module(rel, modules)
        if m:
            return m
        # infer from path
        parts = Path(rel).parts
        cat = guess_category(list(parts))
        under = list(parts[1:-1]) if len(parts) > 1 else []
        return module_id_from_segments(cat, under or [Path(rel).stem], depth=2)

    def canonical_dest(mid: str, filename: str) -> Path:
        cfg = modules.get(mid) or {}
        cat = cfg.get("category") or mid.split(".")[0]
        # Prefer first path glob folder
        paths = cfg.get("paths") or [f"assets/{cat}/**"]
        base = paths[0].split("*")[0].rstrip("/")
        if not base:
            base = f"assets/{cat}/{mid.split('.')[-1].lower()}"
        # if base is category only, append entity folder
        entity = mid.split(".")[-1]
        dest_dir = root / base
        # if glob was assets/character/** and module is character.Astra, use assets/character/astra/
        if base.rstrip("/").count("/") <= 1 and entity:
            dest_dir = root / base / entity.lower()
        return dest_dir / filename

    sources: list[Path] = []
    if plan_all_orphans:
        roots = boot.get("asset_roots") or ["assets"]
        for img in list_image_files(root, roots):
            rel = img.relative_to(root).as_posix()
            if not path_mapped_to_module(rel, {k: v for k, v in modules.items() if v.get("status", "active") in ("active", "scaffold", "candidate")}):
                sources.append(img)
    else:
        p = Path(src)
        if not p.is_absolute():
            p = root / p
        if not p.exists():
            print(f"❌ 文件不存在: {src}")
            return 1
        sources = [p]

    for src_path in sources:
        try:
            rel = src_path.relative_to(root).as_posix()
        except ValueError:
            rel = src_path.name
        mid = infer_module_for(rel)
        if not mid:
            print(f"⚠️ 无法推断模块: {rel}")
            continue
        dest = canonical_dest(mid, src_path.name)
        try:
            dest_rel = dest.relative_to(root).as_posix()
        except ValueError:
            dest_rel = str(dest)
        action = "noop" if src_path.resolve() == dest.resolve() else ("move" if apply else "plan-move")
        plans.append({"src": rel, "dest": dest_rel, "module": mid, "role": role, "action": action})

    print(f"{'执行' if apply else '计划（dry-run）'} place · {len(plans)} 项 · never_auto_move={boot.get('never_auto_move', True)}")
    print(f"{'源':<48} → {'目标':<48} 模块")
    print("-" * 110)
    for pl in plans:
        print(f"{pl['src']:<48} → {pl['dest']:<48} {pl['module']}")

    if not apply:
        print("\n未改动任何文件。确认后加 --apply 执行移动，并建议随后: sync && accept && atlas")
        return 0

    for pl in plans:
        src_path = root / pl["src"]
        dest_path = root / pl["dest"]
        if src_path.resolve() == dest_path.resolve():
            continue
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dest_path))
        print(f"   ✔ moved {pl['src']} → {pl['dest']}")
        # auto-promote candidate if configured
        if (data.get("config") or {}).get("write", {}).get("auto_promote_candidate_on_record", True):
            if pl["module"] not in modules or modules[pl["module"]].get("status") != "active":
                promote_module(
                    root,
                    modules,
                    data.get("categories") or dict(STARTER_CATEGORIES),
                    pl["module"],
                    {"module_id": pl["module"], "paths_glob": [str(Path(pl["dest"]).parent.as_posix()) + "/**"], "category": pl["module"].split(".")[0]},
                    data.get("synonyms"),
                )
                print(f"   ✔ auto-promoted module {pl['module']} → active")
    return 0


def cmd_bootstrap(root: Path, data: dict[str, Any], mode: str, auto_accept_depth: int = 2, apply: bool = False, roots: list[str] | None = None) -> int:
    config = data.get("config") or default_config(mode=mode)
    boot = config.setdefault("bootstrap", {})
    if roots:
        boot["asset_roots"] = roots
    boot["auto_accept_depth"] = auto_accept_depth
    config["project"] = config.get("project") or {}
    config["project"]["lifecycle_mode"] = mode
    config.setdefault("gate", {})["mode"] = "warn" if mode == "young" else "warn"  # warn until confirmed
    write_config_yaml(root, config)

    print(f"🚀 bootstrap --mode {mode}")
    print("═" * 60)

    if mode == "young":
        # Ensure scaffolds + empty dirs
        modules = data.get("modules") or {}
        categories = data.get("categories") or {}
        if not modules:
            modules = {k: dict(v) for k, v in STARTER_MODULES.items()}
            categories = dict(STARTER_CATEGORIES)
            write_modules_yaml(root, categories, modules, data.get("synonyms"))
            print("   · 写入 starter taxonomy（scaffold）")
        for cat in STARTER_CATEGORIES:
            d = root / "assets" / cat
            d.mkdir(parents=True, exist_ok=True)
        ensure_cursor_stubs(root)
        print(f"   · 脚手架目录就绪: assets/{{{','.join(STARTER_CATEGORIES)}}}/")
        print(f"   · gate.mode={config['gate']['mode']}（年轻项目默认 warn，确认模块后再改 block）")
        print(f"   · auto_accept_depth={auto_accept_depth}")
        # sync with optional auto-accept
        data2 = dict(data)
        data2["config"] = config
        data2["modules"] = modules or data.get("modules")
        data2["categories"] = categories or data.get("categories")
        cmd_sync(root, data2, auto_accept_depth=auto_accept_depth, apply_accept=apply)
        if apply:
            boot["confirmed"] = True
            config["gate"]["mode"] = "block"
            config["bootstrap"] = boot
            write_config_yaml(root, config)
            print("   · --apply：已将深度内候选自动提升，并将 gate.mode 切为 block")
        else:
            print("\n保证项（Young）：")
            print("   1) 空项目也有分类脚手架与落盘目录，不是空白黑洞")
            print("   2) 新文件 → sync 提议 candidate（带置信度），默认不静默改 modules.yaml")
            print(f"   3) `--auto-accept-depth {auto_accept_depth}` + `--apply` 才自动接受浅层模块")
            print("   4) place 默认 dry-run；加 --apply 才移动文件")
            print("\n确认脚手架后: python3 pmem_art.py bootstrap --mode young --apply")
        return 0

    if mode == "legacy":
        scan_roots = boot.get("asset_roots") or ["assets"]
        # expand common legacy roots that exist
        discovered_roots = []
        for r in list(scan_roots) + COMMON_LEGACY_ROOTS:
            if (root / r).exists() and r not in discovered_roots:
                discovered_roots.append(r)
        if not discovered_roots:
            discovered_roots = ["assets"]
        boot["asset_roots"] = discovered_roots
        write_config_yaml(root, config)

        print(f"   · 扫描根: {discovered_roots}")
        print("   · 策略: 只提议、不移动文件（never_auto_move=true）")

        clusters = discover_folder_clusters(root, discovered_roots, depth=max(auto_accept_depth, 2))
        candidates = load_candidates_file(root)
        report_lines = [
            f"# pmem-art Legacy Bootstrap Report",
            f"",
            f"- generated_at: {now_iso()}",
            f"- roots: {', '.join(discovered_roots)}",
            f"- clusters: {len(clusters)}",
            f"- policy: propose only (no file moves)",
            f"",
            f"## Proposed modules",
            f"",
        ]
        for c in clusters:
            candidates = merge_candidate(candidates, c)
            # Guess style inheritance: promo vs production
            folder_l = c["folder"].lower()
            style_hint = ""
            if any(x in folder_l for x in ("promo", "marketing", "kv", "keyart", "宣传", "概念")):
                style_hint = " · 可能是宣传/概念向（建议 parent=brand.WorldStyle，勿与生产 UI 混模块）"
            elif any(x in folder_l for x in ("prod", "ingame", "runtime", "export", "导出")):
                style_hint = " · 可能是生产/进游向"
            report_lines.append(
                f"- `{c['module_id']}` conf={c['confidence']} files={c['file_count']} ← `{c['folder']}`{style_hint}"
            )
            for s in c["sample_files"][:3]:
                report_lines.append(f"  - sample: `{s}`")

        # Seed from README / style guides if present
        seed_hits = []
        for pattern in ("**/README.md", "**/StyleGuide.md", "**/风格规范.md", "**/ArtBible.md", "**/*styleguide*"):
            for p in root.glob(pattern):
                if MEMORY_DIR in p.parts:
                    continue
                seed_hits.append(p.relative_to(root).as_posix())
        if seed_hits:
            report_lines += ["", "## Possible style-guide seeds (manual import suggested)", ""]
            for h in seed_hits[:20]:
                report_lines.append(f"- `{h}`")

        save_candidates_file(root, candidates)
        report_path = root / MEMORY_DIR / "LEGACY_BOOTSTRAP_REPORT.md"
        report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

        total_imgs = len(list_image_files(root, discovered_roots))
        modules = data.get("modules") or {}
        mapped = 0
        for img in list_image_files(root, discovered_roots):
            rel = img.relative_to(root).as_posix()
            if path_mapped_to_module(rel, modules):
                mapped += 1
        coverage = (mapped / total_imgs * 100) if total_imgs else 0.0

        print(f"   · 发现图片: {total_imgs}  |  已映射到现有模块: {mapped} ({coverage:.1f}%)")
        print(f"   · 提议候选: {len(clusters)} → 已写入 {MEMORY_DIR}/candidates.json")
        print(f"   · 报告: {report_path}")
        print("\n保证项（Legacy）：")
        print("   1) 默认绝不自动移动/改名现有资产")
        print("   2) 产出候选 modules + 覆盖率报告，需 accept 才写入 active")
        print("   3) place --plan（或 place 默认 dry-run）预览归位；--apply 才执行")
        print("   4) 若发现 StyleGuide/README，仅列入报告，不自动改写记忆")
        print("\n下一步:")
        print("   python3 pmem_art.py candidates")
        print("   python3 pmem_art.py accept --all          # 确认提议")
        print("   python3 pmem_art.py place --plan-orphans  # 预览孤儿归位")
        print("   python3 pmem_art.py place --plan-orphans --apply  # 确认后执行")
        print("   python3 pmem_art.py doctor")

        if apply:
            # Only auto-accept within depth, still never move files
            data2 = dict(data)
            data2["config"] = config
            cmd_sync(root, data2, auto_accept_depth=auto_accept_depth, apply_accept=True)
            boot["confirmed"] = True
            config["bootstrap"] = boot
            config["gate"]["mode"] = "block"
            write_config_yaml(root, config)
            print("   · --apply：已按 depth 提升候选模块；文件仍未被移动")
        return 0

    print(f"❌ 未知 mode: {mode}（young|legacy）")
    return 1


# ---------------------------------------------------------------------------
# Doctor state · lazy hook 巡检（≥48h 才后台跑；默认用户无感）
# ---------------------------------------------------------------------------

DOCTOR_STATE_FILE = "last_doctor.json"
DOCTOR_CLAIM_LOCK = "last_doctor.claim"
DOCTOR_INTERVAL_HOURS = 48.0
DOCTOR_CLAIM_TTL_MINUTES = 30.0
DOCTOR_HOOK_EVENTS = frozenset({"pre-tool", "pre-gen", "stop"})


def _doctor_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


def _doctor_now_str() -> str:
    return _doctor_now().strftime("%Y-%m-%d %H:%M:%S UTC+8")


def doctor_state_path(root: Path) -> Path:
    d = root / MEMORY_DIR / "_profile"
    d.mkdir(parents=True, exist_ok=True)
    return d / DOCTOR_STATE_FILE


def doctor_claim_lock_path(root: Path) -> Path:
    d = root / MEMORY_DIR / "_profile"
    d.mkdir(parents=True, exist_ok=True)
    return d / DOCTOR_CLAIM_LOCK


def load_doctor_state(root: Path) -> dict[str, Any]:
    p = doctor_state_path(root)
    if not p.is_file():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        # Keep corrupt payload as .bak — never silently discard then overwrite memory of last run
        try:
            bak = p.with_suffix(".json.bak")
            if not bak.exists():
                p.replace(bak)
        except Exception:
            pass
        return {}


def save_doctor_state(root: Path, state: dict[str, Any]) -> Path:
    """Atomic write of doctor profile only (never touches entries/modules/assets)."""
    if not isinstance(state, dict):
        raise TypeError("doctor state must be a dict")
    p = doctor_state_path(root)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


def _clear_doctor_claim_lock(root: Path) -> None:
    try:
        doctor_claim_lock_path(root).unlink(missing_ok=True)
    except Exception:
        pass


def parse_doctor_timestamp(text: str) -> datetime | None:
    s = (text or "").strip().replace(" UTC+8", "").strip()
    if not s:
        return None
    slices = (s, s[:19], s[:10])
    for cand in slices:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(cand, fmt)
                return dt.replace(tzinfo=timezone(timedelta(hours=8)))
            except ValueError:
                continue
    return None


def is_doctor_due(root: Path, *, interval_hours: float = DOCTOR_INTERVAL_HOURS) -> bool:
    state = load_doctor_state(root)
    last = parse_doctor_timestamp(str(state.get("last_run_at") or ""))
    if last is None:
        return True
    return (_doctor_now() - last) >= timedelta(hours=interval_hours)


def try_claim_lazy_doctor(
    root: Path,
    *,
    interval_hours: float = DOCTOR_INTERVAL_HOURS,
    claim_ttl_minutes: float = DOCTOR_CLAIM_TTL_MINUTES,
) -> bool:
    """
    Claim a background doctor slot via O_EXCL lock.

    ``last_run_at`` is only written by a successful ``run_doctor_quiet`` — so a
    crashed child does not burn the full 48h window. In-flight is gated by the
    claim lock TTL (default 30m) instead.
    """
    state = load_doctor_state(root)
    now = _doctor_now()
    last = parse_doctor_timestamp(str(state.get("last_run_at") or ""))
    if last is not None and (now - last) < timedelta(hours=interval_hours):
        return False

    lock = doctor_claim_lock_path(root)
    if lock.is_file():
        age_sec = max(0.0, now.timestamp() - lock.stat().st_mtime)
        if age_sec < claim_ttl_minutes * 60.0:
            return False
        _clear_doctor_claim_lock(root)

    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, _doctor_now_str().encode("utf-8"))
        finally:
            os.close(fd)
    except FileExistsError:
        return False
    except Exception:
        return False

    now_s = _doctor_now_str()
    state["claimed_at"] = now_s
    state["status"] = "running"
    save_doctor_state(root, state)
    return True


def collect_doctor_summary(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Structured doctor metrics (no printing). Includes validate signals from ``data``."""
    config = data.get("config") or {}
    boot = config.get("bootstrap") or {}
    roots = boot.get("asset_roots") or ["assets"]
    modules = data.get("modules") or {}
    images = list_image_files(root, roots)
    mapped: list[str] = []
    orphans: list[str] = []
    by_mod: dict[str, int] = defaultdict(int)
    for img in images:
        rel = img.relative_to(root).as_posix()
        mid = path_mapped_to_module(rel, modules)
        if mid:
            mapped.append(rel)
            by_mod[mid] += 1
        else:
            orphans.append(rel)

    total = len(images)
    cov = (len(mapped) / total * 100.0) if total else 100.0
    scaffolds = [m for m, c in modules.items() if c.get("status") == "scaffold"]
    candidates = [c for c in load_candidates_file(root) if c.get("status", "candidate") == "candidate"]
    actives = [m for m, c in modules.items() if c.get("status", "active") == "active"]

    conflicts: list[str] = []
    for mid, cfg in modules.items():
        paths = " ".join(cfg.get("paths") or []).lower()
        if ("promo" in paths or "marketing" in paths) and (
            "ui" in (cfg.get("category") or "") or "hud" in paths
        ):
            conflicts.append(f"{mid}: 宣传向路径与 UI 生产模块可能冲突，建议拆分 parent")

    specs_dir = root / MEMORY_DIR / "specs"
    specs_mods = {
        p.name
        for p in specs_dir.iterdir()
        if p.is_dir() and not is_junk_sidecar_name(p.name)
    } if specs_dir.is_dir() else set()
    entry_mods = {
        str(e.get("module") or "")
        for e in (data.get("entries") or [])
        if isinstance(e, dict) and e.get("module")
    }
    missing_specs = sorted(
        m for m in entry_mods
        if m and m not in specs_mods and not str(m).startswith("vlm.")
    )

    stale_entries = list(data.get("stale_entries") or [])
    qa_issues = list(data.get("qa_issues") or [])

    # 巡检信号：发现问题即记（严格）；是否打扰用户另由 tip_budget 节流
    signals: list[str] = []
    if conflicts:
        signals.append(f"多风格冲突 {len(conflicts)}")
    if orphans:
        signals.append(f"孤儿 {len(orphans)}")
    if cov < 80.0 and total > 0:
        signals.append(f"覆盖率 {cov:.0f}%")
    if stale_entries:
        signals.append(f"STALE {len(stale_entries)}")
    if qa_issues:
        signals.append(f"QA {len(qa_issues)}")
    if missing_specs:
        signals.append(f"缺specs {len(missing_specs)}")

    needs_attention = bool(signals)
    tip_line = None
    if needs_attention:
        tip_line = "🩺 记忆医生：" + " · ".join(signals[:4]) + "（可 `python3 pmem_art.py doctor`）"

    return {
        "lifecycle_mode": (config.get("project") or {}).get("lifecycle_mode", "?"),
        "gate_mode": (config.get("gate") or {}).get("mode", "?"),
        "bootstrap_ok": bool(boot.get("confirmed", False)),
        "last_sync_at": boot.get("last_sync_at"),
        "asset_roots": list(roots),
        "active_modules": len(actives),
        "scaffold_modules": len(scaffolds),
        "candidates_pending": len(candidates),
        "assets_total": total,
        "assets_mapped": len(mapped),
        "orphans": len(orphans),
        "orphan_samples": orphans[:8],
        "coverage_pct": round(cov, 1),
        "specs_dirs": len(specs_mods),
        "missing_specs": missing_specs,
        "conflicts": conflicts,
        "stale_count": len(stale_entries),
        "qa_issue_count": len(qa_issues),
        "signals": signals,
        "needs_attention": needs_attention,
        "tip_line": tip_line,
    }


def print_doctor_summary(summary: dict[str, Any]) -> None:
    print("🩺 pmem-art doctor（覆盖率 · 孤儿 · 生命周期）\n")
    print(f"   lifecycle_mode : {summary.get('lifecycle_mode', '?')}")
    print(f"   gate.mode      : {summary.get('gate_mode', '?')}")
    print(
        f"   bootstrap.ok   : {summary.get('bootstrap_ok', False)}  "
        f"last_sync={summary.get('last_sync_at')}"
    )
    print(f"   asset_roots    : {summary.get('asset_roots') or ['assets']}")
    print(
        f"   modules        : active={summary.get('active_modules', 0)}  "
        f"scaffold={summary.get('scaffold_modules', 0)}  "
        f"candidates_pending={summary.get('candidates_pending', 0)}"
    )
    print(
        f"   assets         : total={summary.get('assets_total', 0)}  "
        f"mapped={summary.get('assets_mapped', 0)}  "
        f"orphans={summary.get('orphans', 0)}  "
        f"coverage={summary.get('coverage_pct', 100.0):.1f}%"
    )
    missing = list(summary.get("missing_specs") or [])
    print(
        f"   specs          : dirs={summary.get('specs_dirs', 0)}  "
        f"entries_missing_specs={len(missing)}"
    )
    samples = list(summary.get("orphan_samples") or [])
    if samples:
        print("\n   孤儿文件样本:")
        for o in samples:
            print(f"      - {o}")
    if missing:
        print("\n   有 entries 但缺 specs/ 目录:")
        for m in missing[:12]:
            print(f"      ⚠️ {m}  → 建议补 `.memory-art/specs/{m}/`（管线规格 / 视觉设定 / 资产台账）")
    conflicts = list(summary.get("conflicts") or [])
    if conflicts:
        print("\n   多风格冲突提示:")
        for c in conflicts:
            print(f"      ⚠️ {c}")
    print("\n   Mode C 持续循环: sync → candidates/accept → search/validate → record → atlas")


def cmd_doctor_lifecycle(root: Path, data: dict[str, Any]) -> int:
    summary = collect_doctor_summary(root, data)
    print_doctor_summary(summary)
    cov = float(summary.get("coverage_pct") or 100.0)
    total = int(summary.get("assets_total") or 0)
    return 0 if cov >= 50 or total == 0 else 0


def run_doctor_quiet(
    root: Path,
    data: dict[str, Any],
    *,
    source: str = "cli",
    offer_tip: bool = True,
) -> dict[str, Any]:
    """
    Inspect-only silent doctor.

    Writes solely ``.memory-art/_profile/last_doctor.json`` (+ clears claim lock).
    Never creates/updates/deletes entries、modules.yaml、assets、specs、library.
    """
    try:
        summary = collect_doctor_summary(root, data)
        needs = bool(summary.get("needs_attention"))
        state = load_doctor_state(root)
        state.update(
            {
                "last_run_at": _doctor_now_str(),
                "claimed_at": "",
                "status": "ok",
                "source": source,
                "needs_attention": needs,
                "tip_pending": bool(needs and offer_tip),
                "tip_line": summary.get("tip_line") or "",
                "signals": list(summary.get("signals") or []),
                "coverage_pct": summary.get("coverage_pct"),
                "orphans": summary.get("orphans"),
                "orphan_samples": list(summary.get("orphan_samples") or [])[:8],
                "stale_count": summary.get("stale_count"),
                "qa_issue_count": summary.get("qa_issue_count"),
                "conflicts": list(summary.get("conflicts") or []),
                "missing_specs": list(summary.get("missing_specs") or [])[:20],
                "missing_specs_count": len(summary.get("missing_specs") or []),
                "inspect_only": True,
            }
        )
        save_doctor_state(root, state)
        return summary
    except Exception:
        state = load_doctor_state(root)
        state["claimed_at"] = ""
        state["status"] = "quiet_failed"
        # Do not stamp last_run_at — allow hook retry after claim lock TTL
        save_doctor_state(root, state)
        raise
    finally:
        _clear_doctor_claim_lock(root)


def spawn_lazy_doctor(root: Path, *, source: str = "hook") -> bool:
    """Fire-and-forget ``doctor --quiet``. Caller must ``try_claim_lazy_doctor`` first."""
    script = Path(__file__).resolve().parent / "pmem_art.py"
    if not script.is_file():
        script = root / "pmem_art.py"
    cmd = [
        sys.executable,
        str(script),
        "--root",
        str(root),
        "doctor",
        "--quiet",
        "--source",
        source,
    ]
    try:
        kwargs: dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "stdin": subprocess.DEVNULL,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
                subprocess, "DETACHED_PROCESS", 0
            )
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(cmd, **kwargs)
        return True
    except Exception:
        # Release in-flight claim only — do not invent a successful last_run_at
        state = load_doctor_state(root)
        state["claimed_at"] = ""
        state["status"] = "spawn_failed"
        save_doctor_state(root, state)
        _clear_doctor_claim_lock(root)
        return False


def consume_doctor_tip(root: Path) -> str | None:
    """If a quiet doctor left a high-signal tip pending, spend tip_budget once per day."""
    state = load_doctor_state(root)
    if not state.get("tip_pending") or not state.get("needs_attention"):
        return None
    tip = str(state.get("tip_line") or "").strip()
    if not tip:
        state["tip_pending"] = False
        save_doctor_state(root, state)
        return None
    try:
        from improve import try_consume_tip_budget
    except Exception:
        state["tip_pending"] = False
        state["tip_error"] = "improve.try_consume_tip_budget unavailable"
        save_doctor_state(root, state)
        return None
    day_key = f"doctor:{_doctor_now().strftime('%Y%m%d')}"
    if not try_consume_tip_budget(root, day_key):
        return None
    state["tip_pending"] = False
    state["tip_consumed_at"] = _doctor_now_str()
    save_doctor_state(root, state)
    return tip


def maybe_lazy_doctor_on_hook(root: Path, event: str) -> str | None:
    """
    On use-hooks: if doctor due (>48h), claim + background spawn.
    Always try to surface at most one high-signal whisper tip (from a finished quiet run).
    Never dumps the full doctor report into the hook message.
    """
    if event not in DOCTOR_HOOK_EVENTS:
        return consume_doctor_tip(root)
    if try_claim_lazy_doctor(root):
        spawn_lazy_doctor(root, source=f"hook:{event}")
    return consume_doctor_tip(root)
