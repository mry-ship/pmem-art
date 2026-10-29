#!/usr/bin/env python3
"""Project-wide image index for the art-atlas workbench.

Visibility-only: scans watch dirs into `.memory-art/atlas_index.json` without
formal module ingest / recipe writes.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_ROUND_NAME_RE = re.compile(r"(?:^|[_-])r\d{1,2}\.", re.IGNORECASE)
_ROUND_ONLY_RE = re.compile(r"^r\d{1,2}\.(png|jpe?g|webp)$", re.IGNORECASE)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_SCAN_PREFIXES = (
    "assets",
    ".cursor/generated",
    "generated",
    ".memory-art/converge",
)
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
}
INDEX_REL = ".memory-art/atlas_index.json"
DATA_REL = ".memory-art/atlas_data.json"
THUMB_DIR_REL = ".memory-art/_thumbs"
THUMB_MAX_EDGE = 360
THUMB_JPEG_QUALITY = 72
CST = timezone(timedelta(hours=8))


def _is_junk_name(name: str) -> bool:
    n = name.lower()
    return (
        n.startswith("._")
        or n in SKIP_DIR_NAMES
        or n.endswith(".pyc")
    )


def classify_source(rel_path: str) -> str:
    p = rel_path.replace("\\", "/")
    if p.startswith("assets/"):
        return "module"
    if p.startswith(".cursor/generated/") or "/.cursor/generated/" in f"/{p}":
        return "cursor_generated"
    if p.startswith("generated/"):
        return "generated"
    if p.startswith(".memory-art/converge/") or "/.memory-art/converge/" in f"/{p}":
        return "converge"
    return "other"


def classify_plate(
    rel_path: str,
    *,
    source: str | None = None,
    role: str | None = None,
) -> str:
    """定稿 / 过程稿 / 废案 / 参考 — 工作台默认只看定稿，避免过程图刷屏。"""
    p = rel_path.replace("\\", "/")
    name = Path(p).name
    src = source or classify_source(p)
    role_l = str(role or "").strip().lower()
    if role_l == "rejected" or "reject" in name.lower():
        return "rejected"
    if role_l == "reference":
        return "reference"
    if src in {"converge", "cursor_generated", "generated", "other"}:
        return "process"
    if "/.memory-art/converge/" in f"/{p}" or "/boards/" in p:
        return "process"
    if _ROUND_ONLY_RE.match(name) or _ROUND_NAME_RE.search(name):
        return "process"
    if role_l in {"draft", "draft_violation"} or "draft" in name.lower():
        return "process"
    # assets 里的 L01–L08 合成梯交货、final、anchor 都算定稿
    return "final"


def day_key_from_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, tz=CST).strftime("%Y-%m-%d")


def day_bucket(day: str, *, today: str | None = None) -> str:
    today = today or datetime.now(CST).strftime("%Y-%m-%d")
    yday = (datetime.now(CST) - timedelta(days=1)).strftime("%Y-%m-%d")
    if day == today:
        return "today"
    if day == yday:
        return "yesterday"
    return "earlier"


def infer_category(rel_path: str, module: str | None = None) -> str:
    if module and "." in module:
        return module.split(".", 1)[0]
    parts = Path(rel_path).parts
    if len(parts) >= 2 and parts[0] == "assets":
        return parts[1]
    return "misc"


def match_module(
    rel_path: str,
    modules: dict[str, Any] | None,
    *,
    png_module: str | None = None,
) -> str:
    if png_module:
        return str(png_module)
    if not modules:
        return "unassigned"
    import fnmatch

    for mod_id, mod_cfg in modules.items():
        if not isinstance(mod_cfg, dict):
            continue
        for pat in mod_cfg.get("paths") or []:
            if fnmatch.fnmatch(rel_path, pat):
                return mod_id
    return "unassigned"


def _light_dims(path: Path) -> dict[str, Any]:
    """Read only headers for size; never embed base64."""
    try:
        from pmem_art import inspect_png

        info = inspect_png(path, embed_data_uri=False)
        return {
            "exists": bool(info.get("exists")),
            "width": info.get("width"),
            "height": info.get("height"),
            "resolution": info.get("resolution") or "",
            "mode": info.get("mode") or "",
            "has_alpha": bool(info.get("has_alpha")),
            "size_kb": info.get("size_kb") or 0,
            "sha256_16": info.get("sha256_16") or "",
            "png_meta": info.get("png_meta") or {},
        }
    except Exception:
        try:
            st = path.stat()
            return {
                "exists": True,
                "width": None,
                "height": None,
                "resolution": "",
                "mode": "",
                "has_alpha": False,
                "size_kb": round(st.st_size / 1024, 1),
                "sha256_16": "",
                "png_meta": {},
            }
        except OSError:
            return {"exists": False}


def iter_scan_files(root: Path, prefixes: tuple[str, ...] | None = None) -> list[Path]:
    root = root.resolve()
    prefixes = prefixes or DEFAULT_SCAN_PREFIXES
    out: list[Path] = []
    for prefix in prefixes:
        base = root / prefix
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            try:
                rel_parts = p.relative_to(root).parts
            except ValueError:
                continue
            if any(_is_junk_name(part) for part in rel_parts):
                continue
            out.append(p)
    out.sort(key=lambda x: x.as_posix())
    return out


def scan_project_images(
    root: Path,
    *,
    modules: dict[str, Any] | None = None,
    prefixes: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Scan watch dirs into a visibility index (does not ingest / write recipe)."""
    root = root.resolve()
    today = datetime.now(CST).strftime("%Y-%m-%d")
    items: list[dict[str, Any]] = []
    for abs_p in iter_scan_files(root, prefixes=prefixes):
        rel = abs_p.relative_to(root).as_posix()
        try:
            st = abs_p.stat()
        except OSError:
            continue
        dims = _light_dims(abs_p)
        png_mod = None
        meta = dims.get("png_meta") if isinstance(dims.get("png_meta"), dict) else {}
        if meta:
            png_mod = meta.get("pmem_module")
        mod = match_module(rel, modules, png_module=str(png_mod) if png_mod else None)
        source = classify_source(rel)
        day = day_key_from_mtime(st.st_mtime)
        cat = infer_category(rel, mod if mod != "unassigned" else None)
        if source != "module" and mod == "unassigned":
            cat = "misc"
        role = ""
        if isinstance(meta, dict):
            role = str(meta.get("pmem_role") or "")
        plate = classify_plate(rel, source=source, role=role)
        items.append(
            {
                "path": rel,
                "mtime": st.st_mtime,
                "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=CST).strftime("%Y-%m-%d %H:%M"),
                "day": day,
                "day_bucket": day_bucket(day, today=today),
                "bytes": st.st_size,
                "size_kb": dims.get("size_kb") or round(st.st_size / 1024, 1),
                "width": dims.get("width"),
                "height": dims.get("height"),
                "resolution": dims.get("resolution") or "",
                "mode": dims.get("mode") or "",
                "has_alpha": bool(dims.get("has_alpha")),
                "sha256_16": dims.get("sha256_16") or "",
                "source": source,
                "module": mod,
                "category": cat,
                "role": role or ("draft" if plate == "process" else "approved"),
                "plate": plate,
                "formal": source == "module" and mod != "unassigned" and plate == "final",
            }
        )
    items.sort(key=lambda x: (-float(x.get("mtime") or 0), str(x.get("path") or "")))
    return items


def build_index_payload(
    root: Path,
    images: list[dict[str, Any]] | None = None,
    *,
    modules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    imgs = images if images is not None else scan_project_images(root, modules=modules)
    today = datetime.now(CST).strftime("%Y-%m-%d")
    counts = {
        "today": 0,
        "yesterday": 0,
        "earlier": 0,
        "by_source": {},
        "by_category": {},
        "by_plate": {},
    }
    for it in imgs:
        b = it.get("day_bucket") or day_bucket(str(it.get("day") or ""), today=today)
        counts[b] = counts.get(b, 0) + 1
        src = str(it.get("source") or "other")
        counts["by_source"][src] = counts["by_source"].get(src, 0) + 1
        cat = str(it.get("category") or "misc")
        counts["by_category"][cat] = counts["by_category"].get(cat, 0) + 1
        plate = str(it.get("plate") or classify_plate(str(it.get("path") or ""), source=src, role=str(it.get("role") or "")))
        it["plate"] = plate
        counts["by_plate"][plate] = counts["by_plate"].get(plate, 0) + 1
    sig = hashlib.sha256(
        json.dumps([(i.get("path"), i.get("mtime"), i.get("sha256_16")) for i in imgs], sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "schema_version": 1,
        "root": str(root),
        "built_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S UTC+8"),
        "today": today,
        "index_id": sig,
        "images_count": len(imgs),
        "counts": counts,
        "images": imgs,
        "note": "visibility index only — does not formal-ingest into modules/recipes",
    }


def write_atlas_index(
    root: Path,
    images: list[dict[str, Any]] | None = None,
    *,
    modules: dict[str, Any] | None = None,
) -> Path:
    root = root.resolve()
    payload = build_index_payload(root, images, modules=modules)
    out = root / INDEX_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def thumb_cache_rel(rel_path: str, mtime: float | int | None) -> str:
    """Stable relative path for a gallery JPEG thumb (invalidates on mtime change)."""
    key = hashlib.sha1(f"{rel_path}|{float(mtime or 0):.3f}".encode("utf-8")).hexdigest()[:20]
    return f"{THUMB_DIR_REL}/{key}.jpg"


def _write_one_thumb(src: Path, dest: Path, max_edge: int = THUMB_MAX_EDGE) -> bool:
    try:
        from PIL import Image
    except ImportError:
        return False
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
            if im.mode == "RGBA":
                bg = Image.new("RGB", im.size, (11, 16, 29))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            else:
                im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_edge:
                im.thumbnail((max_edge, max_edge), Image.Resampling.BILINEAR)
            im.save(dest, format="JPEG", quality=THUMB_JPEG_QUALITY, optimize=True)
        return dest.is_file()
    except Exception:
        return False


def ensure_gallery_thumbs(
    root: Path,
    assets: dict[str, Any],
    *,
    max_edge: int = THUMB_MAX_EDGE,
    workers: int = 8,
) -> dict[str, int]:
    """Ensure JPEG thumbs for gallery cards; set ``thumb`` on each asset dict.

    Large originals decode slowly in the browser; gallery uses these ~360px JPEGs.
    Viewer still opens the original via ``path``.
    """
    root = root.resolve()
    stats = {"created": 0, "cached": 0, "skipped": 0, "failed": 0}
    jobs: list[tuple[str, Path, Path, dict[str, Any]]] = []
    for rel, info in (assets or {}).items():
        if not isinstance(info, dict):
            continue
        rel_s = str(info.get("path") or rel or "").replace("\\", "/")
        if not rel_s:
            stats["skipped"] += 1
            continue
        src = root / rel_s
        if not src.is_file():
            info.pop("thumb", None)
            stats["skipped"] += 1
            continue
        w = int(info.get("width") or 0)
        h = int(info.get("height") or 0)
        size_kb = float(info.get("size_kb") or 0)
        # Already small enough — no need for a separate thumb file
        if (w and h and max(w, h) <= max_edge and size_kb <= 120) or size_kb <= 40:
            info.pop("thumb", None)
            stats["skipped"] += 1
            continue
        mtime = info.get("mtime")
        if mtime is None:
            try:
                mtime = src.stat().st_mtime
            except OSError:
                mtime = 0
        thumb_rel = thumb_cache_rel(rel_s, float(mtime or 0))
        dest = root / thumb_rel
        if dest.is_file():
            info["thumb"] = thumb_rel
            stats["cached"] += 1
            continue
        jobs.append((rel_s, src, dest, info))

    if not jobs:
        return stats

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _task(job: tuple[str, Path, Path, dict[str, Any]]) -> tuple[dict[str, Any], str | None]:
        rel_s, src, dest, info = job
        ok = _write_one_thumb(src, dest, max_edge=max_edge)
        if not ok:
            return info, None
        return info, thumb_cache_rel(rel_s, float(info.get("mtime") or 0))

    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(jobs)))) as pool:
        futs = [pool.submit(_task, j) for j in jobs]
        for fut in as_completed(futs):
            try:
                info, thumb_rel = fut.result()
            except Exception:
                stats["failed"] += 1
                continue
            if thumb_rel:
                info["thumb"] = thumb_rel
                stats["created"] += 1
            else:
                info.pop("thumb", None)
                stats["failed"] += 1
    return stats


def write_atlas_data_sidecar(root: Path, data: dict[str, Any]) -> Path:
    """Slim JSON for workbench hot-reload (no data_uri blobs)."""
    root = root.resolve()
    slim = dict(data)
    assets = {}
    for path, info in (data.get("assets") or {}).items():
        if not isinstance(info, dict):
            continue
        assets[path] = {k: v for k, v in info.items() if k != "data_uri"}
    slim["assets"] = assets
    out = root / DATA_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(slim, ensure_ascii=False).replace("</", "<\\/"), encoding="utf-8")
    return out


def merge_index_into_assets(
    assets_info: dict[str, dict[str, Any]],
    images: list[dict[str, Any]],
    *,
    categories: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Union scanned images into assets_info for the gallery. Does not write memory."""
    default_cat = {
        "brand": {"label": "全局风格圣经", "short": "风格圣经", "icon": "🎨"},
        "character": {"label": "角色与立绘", "short": "角色与立绘", "icon": "🧝‍♀️"},
        "scene": {"label": "场景与原画", "short": "场景与原画", "icon": "🏯"},
        "ui": {"label": "UI与九宫格", "short": "UI与九宫格", "icon": "💠"},
        "vfx": {"label": "特效与序列帧", "short": "特效与序列帧", "icon": "✨"},
        "anim": {"label": "骨骼与动画", "short": "骨骼与动画", "icon": "🦴"},
        "misc": {"label": "其他 / 散图（仅工作台可见）", "short": "其他", "icon": "📦"},
    }
    cats = categories or {}
    for it in images:
        rel = str(it.get("path") or "")
        if not rel:
            continue
        existing = assets_info.get(rel)
        cat = str(it.get("category") or "misc")
        cat_m = cats.get(cat) or default_cat.get(cat) or default_cat["misc"]
        plate = str(
            it.get("plate")
            or classify_plate(rel, source=str(it.get("source") or ""), role=str(it.get("role") or (existing or {}).get("role") or ""))
        )
        patch = {
            "path": rel,
            "mtime": it.get("mtime"),
            "day": it.get("day"),
            "day_bucket": it.get("day_bucket"),
            "source": it.get("source") or "other",
            "plate": plate,
            "formal": bool(it.get("formal")) if it.get("formal") is not None else plate == "final",
            "updated_at": it.get("mtime_iso") or "",
            "size_kb": it.get("size_kb"),
            "width": it.get("width"),
            "height": it.get("height"),
            "resolution": it.get("resolution") or (existing or {}).get("resolution") or "",
            "mode": it.get("mode") or (existing or {}).get("mode") or "",
            "has_alpha": it.get("has_alpha") if it.get("has_alpha") is not None else (existing or {}).get("has_alpha"),
            "sha256_16": it.get("sha256_16") or (existing or {}).get("sha256_16") or "",
            "category": cat if not existing else (existing.get("category") or cat),
            "category_label": (existing or {}).get("category_label") or cat_m.get("label", cat),
            "category_short": (existing or {}).get("category_short") or cat_m.get("short", cat),
            "category_icon": (existing or {}).get("category_icon") or cat_m.get("icon", "📦"),
        }
        if existing:
            existing.update({k: v for k, v in patch.items() if v is not None and v != ""})
            existing.setdefault("module", it.get("module") or "unassigned")
            existing.pop("data_uri", None)
        else:
            src = it.get("source") or "other"
            src_label = {
                "cursor_generated": "Cursor 生图",
                "generated": "generated",
                "converge": "收敛过程",
                "module": "模块资产",
                "other": "散图",
            }.get(str(src), "散图")
            assets_info[rel] = {
                "exists": True,
                "path": rel,
                "module": it.get("module") or "unassigned",
                "module_title": it.get("module") if it.get("module") not in (None, "unassigned") else src_label,
                "role": "draft" if src != "module" else "approved",
                "description": f"{src_label} · {Path(rel).name}",
                "prompt": "",
                "qa_issues": [],
                "qa_passed": True,
                "qa_intentional_reject": False,
                "linked_entry_ids": [],
                "png_meta": {},
                **patch,
            }
            assets_info[rel].pop("data_uri", None)
    # 记忆条目带进来的路径也可能没有 plate，统一补齐
    for rel, info in list(assets_info.items()):
        if not isinstance(info, dict):
            continue
        if info.get("plate"):
            continue
        info["plate"] = classify_plate(
            rel,
            source=str(info.get("source") or ""),
            role=str(info.get("role") or (info.get("png_meta") or {}).get("pmem_role") or ""),
        )
    return assets_info


def reveal_in_os(path: Path) -> int:
    """Open the system file manager and select ``path`` (Finder / Explorer)."""
    import subprocess
    import sys

    target = path.expanduser().resolve()
    if not target.exists():
        print(f"❌ 文件不存在: {target}", file=sys.stderr)
        return 1
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(target)], check=False)
        elif sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{target}"], check=False)
        else:
            subprocess.run(["xdg-open", str(target.parent)], check=False)
    except OSError as exc:
        print(f"❌ 无法打开文件夹: {exc}", file=sys.stderr)
        return 1
    print(f"📁 已在文件管理器中定位: {target}")
    return 0
