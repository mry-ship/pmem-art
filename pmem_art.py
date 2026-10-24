#!/usr/bin/env python3
"""
pmem-art: 画师在 Cursor 里越画越准的个人美术积累记忆。

心智模型（不是审稿台 / 不是 CLI 流水线）：
  生图 → 你用自然语言说「哪里不对 / 这版留着 / 换成水彩」→ 记忆长大 → 下次生图自动召回 → 更准。

classify / ingest / domains 仍在后端默默工作；日常入口是 Cursor 对话 + Skills。
v0.12：静默自动驾驶（Whisper Autopilot）· 一行小提示 · Warm-Start / coach/learn 进阶 peek。
零第三方强依赖（Python 3.10+ 标准库）。
"""
from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import json
import os
import re
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

VERSION = "0.13.0-art"
MEMORY_DIR = ".memory-art"

KIND_META = {
    "style_redline":       {"label": "风格红线 (Redline)",      "layer": "lesson", "badge": "danger",  "order": 1},
    "pipeline_constraint": {"label": "管线规范 (Pipeline)",     "layer": "lesson", "badge": "warning", "order": 2},
    "visual_correction":   {"label": "视觉勘误 (Correction)",   "layer": "lesson", "badge": "purple",  "order": 3},
    "art_decision":        {"label": "主美拍板 (Art Decision)", "layer": "lesson", "badge": "teal",    "order": 4},
    "recipe":              {"label": "AI生图配方 (AI Recipe)",  "layer": "lesson", "badge": "gold",    "order": 5},
    "asset_record":        {"label": "资产台账 (Asset Record)", "layer": "record", "badge": "success", "order": 6},
    "art_plan":            {"label": "待产需求 (Art Plan)",     "layer": "record", "badge": "info",    "order": 7},
}

def parse_scalar(val: str) -> Any:
    val = val.strip()
    if not val:
        return ""
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    if val.startswith("{") and val.endswith("}"):
        try:
            return json.loads(val)
        except Exception:
            inner = val[1:-1].strip()
            d: dict[str, Any] = {}
            for part in re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', inner):
                if ":" in part:
                    pk, _, pv = part.partition(":")
                    d[pk.strip().strip('"').strip("'")] = parse_scalar(pv)
            return d
    if val.startswith("[") and val.endswith("]"):
        try:
            return json.loads(val)
        except Exception:
            inner = val[1:-1].strip()
            if not inner:
                return []
            return [parse_scalar(x) for x in re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', inner)]
    low = val.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none", "~"):
        return None
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    if re.fullmatch(r"-?\d+\.\d+", val):
        return float(val)
    return val

def load_yaml(text: str) -> dict:
    try:
        import yaml
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        s = raw_line.rstrip()
        if not s.strip() or s.strip().startswith("#"):
            continue
        # Strip inline comments outside quotes (prevents "true # comment" pollution)
        in_q = None
        out_chars: list[str] = []
        i = 0
        while i < len(s):
            ch = s[i]
            if in_q:
                out_chars.append(ch)
                if ch == in_q and s[i - 1] != "\\":
                    in_q = None
            else:
                if ch in ('"', "'"):
                    in_q = ch
                    out_chars.append(ch)
                elif ch == "#":
                    break
                else:
                    out_chars.append(ch)
            i += 1
        s = "".join(out_chars).rstrip()
        if not s.strip():
            continue
        indent = len(s) - len(s.lstrip(" "))
        lines.append((indent, s.strip()))

    def parse_block(idx: int, min_indent: int) -> tuple[Any, int]:
        if idx >= len(lines):
            return {}, idx
        first_indent, first_content = lines[idx]
        if first_indent < min_indent:
            return {}, idx
        is_list = first_content.startswith("- ") or first_content == "-"
        if is_list:
            arr: list[Any] = []
            while idx < len(lines):
                ind, content = lines[idx]
                if ind != first_indent or not (content.startswith("- ") or content == "-"):
                    break
                rest = content[1:].strip()
                idx += 1
                if not rest:
                    sub, idx = parse_block(idx, ind + 1)
                    arr.append(sub)
                elif rest.startswith("{") and rest.endswith("}"):
                    arr.append(parse_scalar(rest))
                elif ":" in rest and not (rest.startswith('"') or rest.startswith("'")):
                    k, _, v = rest.partition(":")
                    k = k.strip().strip('"').strip("'")
                    v = v.strip()
                    item: dict[str, Any] = {}
                    if v:
                        item[k] = parse_scalar(v)
                    else:
                        sub, idx = parse_block(idx, ind + 1)
                        item[k] = sub
                    while idx < len(lines) and lines[idx][0] > ind:
                        sub_ind, sub_c = lines[idx]
                        if sub_c.startswith("- "):
                            break
                        sk, _, sv = sub_c.partition(":")
                        sk = sk.strip().strip('"').strip("'")
                        sv = sv.strip()
                        idx += 1
                        if sv:
                            item[sk] = parse_scalar(sv)
                        else:
                            sub_v, idx = parse_block(idx, sub_ind + 1)
                            item[sk] = sub_v
                    arr.append(item)
                else:
                    arr.append(parse_scalar(rest))
            return arr, idx
        else:
            obj: dict[str, Any] = {}
            while idx < len(lines):
                ind, content = lines[idx]
                if ind < first_indent:
                    break
                if ind > first_indent:
                    idx += 1
                    continue
                if content.startswith("- ") or ":" not in content:
                    break
                k, _, v = content.partition(":")
                k = k.strip().strip('"').strip("'")
                v = v.strip()
                idx += 1
                if v in ("|", ">"):
                    ml: list[str] = []
                    while idx < len(lines) and lines[idx][0] > ind:
                        ml.append(lines[idx][1])
                        idx += 1
                    obj[k] = ("\n" if v == "|" else " ").join(ml)
                elif v:
                    obj[k] = parse_scalar(v)
                else:
                    sub, idx = parse_block(idx, ind + 1)
                    obj[k] = sub
            return obj, idx

    res, _ = parse_block(0, 0)
    return res if isinstance(res, dict) else {}

def inspect_png(path: Path) -> dict[str, Any]:
    """Pure-Python PNG header & tEXt chunk inspector + outer border alpha checker."""
    if not path.is_file():
        return {"exists": False, "path": str(path)}
    raw = path.read_bytes()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    size_kb = round(len(raw) / 1024, 1)
    b64_uri = "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return {"exists": True, "size_kb": size_kb, "sha256_16": sha16, "data_uri": b64_uri}

    pos = 8
    width = height = bit_depth = color_type = 0
    text_meta: dict[str, Any] = {}
    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        chunk_type = raw[pos + 4:pos + 8]
        chunk_data = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR" and len(chunk_data) >= 13:
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk_data[:10])
        elif chunk_type == b"tEXt":
            if b"\x00" in chunk_data:
                k_raw, v_raw = chunk_data.split(b"\x00", 1)
                k = k_raw.decode("latin1", errors="replace")
                v = v_raw.decode("utf-8", errors="replace")
                try:
                    text_meta[k] = json.loads(v)
                except Exception:
                    text_meta[k] = v
        elif chunk_type == b"IEND":
            break

    mode_map = {0: "L", 2: "RGB", 3: "P", 4: "LA", 6: "RGBA"}
    mode = mode_map.get(color_type, f"Type{color_type}")
    has_alpha = color_type in (4, 6)
    return {
        "exists": True,
        "width": width,
        "height": height,
        "resolution": f"{width}x{height}",
        "bit_depth": bit_depth,
        "mode": mode,
        "has_alpha": has_alpha,
        "size_kb": size_kb,
        "sha256_16": sha16,
        "png_meta": text_meta,
        "data_uri": b64_uri,
    }

def _parse_entry_md_file(
    md_file: Path,
    rel_base: Path,
    *,
    project_id: str,
    project_name: str,
) -> dict[str, Any] | None:
    try:
        raw = md_file.read_text(encoding="utf-8")
    except Exception:
        return None
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", raw, re.DOTALL)
    if not m:
        return None
    meta = load_yaml(m.group(1))
    body = m.group(2).strip()
    meta["body"] = body
    try:
        meta["file_path"] = str(md_file.relative_to(rel_base))
    except Exception:
        meta["file_path"] = str(md_file)
    k_info = KIND_META.get(meta.get("kind", ""), {"label": meta.get("kind", ""), "layer": "lesson", "badge": "info", "order": 9})
    meta["kind_label"] = k_info["label"]
    meta["layer"] = k_info["layer"]
    meta["badge"] = k_info["badge"]
    meta["kind_order"] = k_info["order"]
    meta["layer_scope"] = "private"
    meta["project_id"] = project_id
    meta["project_name"] = project_name
    return meta


def _load_all_project_libraries(
    root: Path,
    active_meta: dict[str, Any],
    assets_info: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    mem_dir = root / MEMORY_DIR
    projects_dir = mem_dir / "projects"
    if not projects_dir.is_dir():
        return []
    active_pid = str(active_meta.get("project_id") or "")
    libs: list[dict[str, Any]] = []
    for lib_dir in sorted(projects_dir.iterdir()):
        if not lib_dir.is_dir():
            continue
        lib_meta: dict[str, Any] = {}
        for mf in ("library.json", "library_meta.json"):
            mp = lib_dir / mf
            if mp.is_file():
                try:
                    lib_meta = json.loads(mp.read_text(encoding="utf-8"))
                    break
                except Exception:
                    pass
        pid = str(lib_meta.get("project_id") or lib_dir.name)
        pname = str(lib_meta.get("project_name") or pid)
        if not lib_meta.get("project_name") and (lib_dir / "config.yaml").is_file():
            try:
                cfg_y = load_yaml((lib_dir / "config.yaml").read_text(encoding="utf-8"))
                pname = str((cfg_y.get("project") or {}).get("name") or pname)
            except Exception:
                pass
        is_current = (pid == active_pid)

        lib_mods: dict[str, Any] = {}
        if (lib_dir / "modules.yaml").is_file():
            try:
                lib_mods = (load_yaml((lib_dir / "modules.yaml").read_text(encoding="utf-8")) or {}).get("modules", {})
            except Exception:
                lib_mods = {}

        lib_entries: list[dict[str, Any]] = []
        lib_entries_dir = lib_dir / "entries"
        if lib_entries_dir.is_dir():
            for md_f in sorted(lib_entries_dir.rglob("*.md")):
                em = _parse_entry_md_file(md_f, root, project_id=pid, project_name=pname)
                if not em:
                    continue
                em["is_historical_project"] = not is_current
                for a in em.get("assets") or []:
                    if isinstance(a, dict) and a.get("path"):
                        actual = assets_info.get(a["path"], {})
                        if actual:
                            a["actual"] = {k: v for k, v in actual.items() if k != "data_uri"}
                lib_entries.append(em)

        lib_kcards: list[dict[str, Any]] = []
        kf = lib_dir / "_knowledge" / "index.json"
        if kf.is_file():
            try:
                kd = json.loads(kf.read_text(encoding="utf-8"))
                for c in (kd.get("cards") or {}).values():
                    if isinstance(c, dict):
                        cc = dict(c)
                        cc["layer_scope"] = "private"
                        cc["project_id"] = pid
                        cc["project_name"] = pname
                        lib_kcards.append(cc)
            except Exception:
                pass

        lib_taste: dict[str, Any] = {}
        tf = lib_dir / "_profile" / "taste.json"
        if tf.is_file():
            try:
                lib_taste = json.loads(tf.read_text(encoding="utf-8"))
                lib_taste["project_id"] = pid
                lib_taste["project_name"] = pname
            except Exception:
                pass

        lib_refls: list[dict[str, Any]] = []
        rd = lib_dir / "_reflections"
        if rd.is_dir():
            for rf in sorted(rd.glob("*.json"), key=lambda x: x.name, reverse=True)[:15]:
                try:
                    ro = json.loads(rf.read_text(encoding="utf-8"))
                    ro.setdefault("project_id", pid)
                    ro.setdefault("project_name", pname)
                    lib_refls.append(ro)
                except Exception:
                    pass

        libs.append({
            "project_id": pid,
            "project_slug": pid,
            "project_name": pname,
            "is_current": is_current,
            "layer_scope": "private",
            "library_dir": f".memory-art/projects/{pid}",
            "origin_root": str(lib_meta.get("origin_root") or lib_meta.get("bound_root") or ""),
            "copied_from_project": str(lib_meta.get("copied_from_project") or ""),
            "created_at": str(lib_meta.get("created_at") or ""),
            "updated_at": str(lib_meta.get("updated_at") or ""),
            "modules_count": len(lib_mods),
            "entries_count": len(lib_entries),
            "entries": lib_entries,
            "knowledge_cards": lib_kcards,
            "taste": lib_taste,
            "reflections": lib_refls,
        })

    libs.sort(key=lambda x: (0 if x.get("is_current") else 1, x.get("project_id", "")))
    return libs


def load_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    mem_dir = root / MEMORY_DIR
    active_meta: dict[str, Any] = {}
    if mem_dir.is_dir():
        try:
            from improve import ensure_project_library_bound
            active_meta = ensure_project_library_bound(root)
        except Exception:
            active_meta = {}

    config = load_yaml((mem_dir / "config.yaml").read_text(encoding="utf-8")) if (mem_dir / "config.yaml").exists() else {}
    modules_doc = load_yaml((mem_dir / "modules.yaml").read_text(encoding="utf-8")) if (mem_dir / "modules.yaml").exists() else {}
    categories = modules_doc.get("categories", {})
    modules = modules_doc.get("modules", {})
    synonyms = modules_doc.get("synonyms", [])

    active_pid = str(active_meta.get("project_id") or root.name.lower())
    active_pname = str(
        active_meta.get("project_name")
        or (config.get("project") or {}).get("name")
        or root.name
    )
    active_meta["project_id"] = active_pid
    active_meta["project_slug"] = active_pid
    active_meta["project_name"] = active_pname
    active_meta.setdefault("layer_scope", "private")
    active_meta.setdefault("bound_root", str(root))
    active_meta.setdefault("library_dir", f".memory-art/projects/{active_pid}")

    # Load entries of the CURRENT active project only
    entries: list[dict[str, Any]] = []
    entries_dir = mem_dir / "entries"
    if entries_dir.is_dir():
        for md_file in sorted(entries_dir.rglob("*.md")):
            em = _parse_entry_md_file(md_file, root, project_id=active_pid, project_name=active_pname)
            if em:
                entries.append(em)

    if mem_dir.is_dir():
        try:
            from improve import sync_active_project_to_library
            sync_active_project_to_library(root, project_name=active_pname)
        except Exception:
            pass

    # Load specs
    specs: dict[str, dict[str, str]] = {}
    specs_dir = mem_dir / "specs"
    if specs_dir.is_dir():
        for mod_dir in sorted(specs_dir.iterdir()):
            if mod_dir.is_dir():
                specs[mod_dir.name] = {}
                for sf in sorted(mod_dir.glob("*.md")):
                    specs[mod_dir.name][sf.stem] = sf.read_text(encoding="utf-8").strip()

    # Load workflows
    workflows: dict[str, Any] = {}
    wf_dir = root / "workflows"
    if wf_dir.is_dir():
        for wf in sorted(wf_dir.glob("*.json")):
            try:
                workflows[f"workflows/{wf.name}"] = json.loads(wf.read_text(encoding="utf-8"))
            except Exception:
                pass

    # Inspect all assets & check staleness / QA rules
    asset_Set: set[str] = set()
    for p in sorted((root / "assets").rglob("*.png")) if (root / "assets").is_dir() else []:
        asset_Set.add(str(p.relative_to(root)).replace("\\", "/"))
    for e in entries:
        for a in e.get("assets") or []:
            if isinstance(a, dict) and a.get("path"):
                asset_Set.add(a["path"])

    assets_info: dict[str, dict[str, Any]] = {}
    for rel_path in sorted(asset_Set):
        info = inspect_png(root / rel_path)
        info["path"] = rel_path
        # Match module by path glob or png_meta
        matched_mod = info.get("png_meta", {}).get("pmem_module")
        if not matched_mod:
            for mod_id, mod_cfg in modules.items():
                for pat in mod_cfg.get("paths", []):
                    if fnmatch.fnmatch(rel_path, pat):
                        matched_mod = mod_id
                        break
        info["module"] = matched_mod or "unassigned"
        assets_info[rel_path] = info

    # Run QA validation per asset against its module's specs
    qa_issues: list[dict[str, Any]] = []
    for rel_path, info in assets_info.items():
        mod_id = info["module"]
        mod_cfg = modules.get(mod_id, {})
        mspecs = mod_cfg.get("specs", {})
        issues: list[str] = []
        if not info.get("exists"):
            issues.append("文件缺失 (File Missing)")
        else:
            allowed_res = mspecs.get("allowed_resolutions") or ([mspecs["resolution"]] if mspecs.get("resolution") else [])
            if allowed_res and info.get("resolution") not in allowed_res:
                issues.append(f"分辨率不符：当前 {info.get('resolution')}，模块要求 {' / '.join(allowed_res)}")
            if mspecs.get("alpha_required") and not info.get("has_alpha"):
                issues.append(f"缺失透明通道：当前色彩模式为 {info.get('mode')}，模块要求 RGBA 透明通道")
            if mspecs.get("max_size_kb") and info.get("size_kb", 0) > mspecs["max_size_kb"]:
                issues.append(f"文件体积超标：当前 {info.get('size_kb')} KB > 上限 {mspecs['max_size_kb']} KB")
        info["qa_issues"] = issues
        info["qa_passed"] = len(issues) == 0
        if issues:
            qa_issues.append({"path": rel_path, "module": mod_id, "issues": issues})

    # Check staleness on entries (compare recorded sha256_16 & QA status of anchored assets)
    stale_entries: list[dict[str, Any]] = []
    for e in entries:
        reasons: list[str] = []
        for a in e.get("assets") or []:
            if not isinstance(a, dict):
                continue
            ap = a.get("path", "")
            expected_sha = a.get("sha256_16")
            actual = assets_info.get(ap, {})
            if expected_sha and actual.get("sha256_16") and expected_sha != actual.get("sha256_16"):
                reasons.append(f"关联图片 {ap} 哈希已变更（记录 {expected_sha[:8]}… → 当前 {actual['sha256_16'][:8]}…）")
            if actual.get("qa_issues"):
                reasons.append(f"关联图片 {ap} 存在管线违规：{'；'.join(actual['qa_issues'])}")
            a["actual"] = {k: v for k, v in actual.items() if k != "data_uri"}
        e["stale"] = len(reasons) > 0
        e["stale_reasons"] = reasons
        if e["stale"]:
            stale_entries.append({"id": e["id"], "module": e["module"], "summary": e.get("summary"), "reasons": reasons})

    # Enrich each asset with category, human description, prompt, role, and linked entries
    from datetime import datetime, timezone, timedelta
    cst = timezone(timedelta(hours=8))
    default_cat_meta = {
        "brand":     {"label": "全局风格圣经 (Brand & Style Bible)",   "short": "风格圣经",   "icon": "🎨"},
        "character": {"label": "角色与立绘绑定 (Character & Rigging)", "short": "角色与立绘", "icon": "🧝‍♀️"},
        "scene":     {"label": "场景与地块物件 (Scene & Environment)", "short": "场景与原画", "icon": "🏯"},
        "ui":        {"label": "界面与九宫格图标 (UI & 9-Slice HUD)",  "short": "UI与九宫格", "icon": "💠"},
        "vfx":       {"label": "特效与序列帧表现 (VFX & Shaders)",     "short": "特效与序列帧", "icon": "✨"},
        "anim":      {"label": "骨骼与帧动画 (Animation & Spine)",     "short": "骨骼与动画", "icon": "🦴"},
        "misc":      {"label": "未归类 / 待提升 (Misc)",               "short": "待归类资产", "icon": "📦"},
    }
    for ck, cv in default_cat_meta.items():
        if ck not in categories:
            categories[ck] = {"label": cv["label"], "icon": cv["icon"], "short": cv["short"]}
        else:
            categories[ck].setdefault("short", cv["short"])
            categories[ck].setdefault("icon", cv["icon"])

    for rel_path, info in assets_info.items():
        mod_id = info.get("module") or "unassigned"
        mod_cfg = modules.get(mod_id, {})
        cat_key = mod_cfg.get("category") or (mod_id.split(".")[0] if "." in mod_id else "")
        if not cat_key or cat_key == "unassigned":
            parts = Path(rel_path).parts
            cat_key = parts[1] if len(parts) > 2 and parts[0] == "assets" else "misc"
        cat_m = categories.get(cat_key) or default_cat_meta.get(cat_key) or {"label": cat_key, "short": cat_key, "icon": "📦"}
        info["category"] = cat_key
        info["category_label"] = cat_m.get("label", cat_key)
        info["category_short"] = cat_m.get("short") or str(cat_m.get("label", cat_key)).split(" (")[0]
        info["category_icon"] = cat_m.get("icon", "📦")
        info["module_title"] = mod_cfg.get("title") or mod_id

        linked = [
            e for e in entries
            if any(isinstance(x, dict) and x.get("path") == rel_path for x in (e.get("assets") or []))
            or any(rel_path in str(anc) for anc in (e.get("anchors") or []))
        ]
        info["linked_entry_ids"] = [e.get("id") for e in linked if e.get("id")]

        # Determine effective role, description, and prompt
        pmeta = info.get("png_meta") or {}
        role = pmeta.get("pmem_role") or ""
        best_desc = ""
        best_prompt = pmeta.get("prompt") or ""
        score_val = None

        for e in linked:
            ai_p = e.get("ai_params") if isinstance(e.get("ai_params"), dict) else {}
            if not best_prompt and ai_p.get("prompt"):
                best_prompt = str(ai_p.get("prompt"))
            if score_val is None and ai_p.get("score") is not None:
                score_val = ai_p.get("score")
            # Check body for - prompt: ...
            if not best_prompt and e.get("body"):
                pm = re.search(r"^-\s*prompt:\s*(.+)$", str(e.get("body")), re.M)
                if pm:
                    best_prompt = pm.group(1).strip()
            for a_item in (e.get("assets") or []):
                if isinstance(a_item, dict) and a_item.get("path") == rel_path:
                    if not role and a_item.get("role"):
                        role = str(a_item.get("role"))
                    cap = str(a_item.get("caption") or "").strip()
                    # Replace generic stub captions with rich summary/prompt
                    if cap.startswith("ingest conf=") or cap in ("✅ 正例（画师确认保留）", "❌ 反例（画师打回）", "参考图"):
                        if best_prompt:
                            cap = f"✅ {best_prompt} · 自动归类：{info[category_short]} ({mod_id})"
                        elif e.get("summary") and not str(e.get("summary")).startswith("自动入库资产 "):
                            prefix = "✅ 正例定稿：" if role == "approved" else ("❌ 反例警示：" if role == "rejected" else "📌 ")
                            cap = prefix + str(e.get("summary"))
                    if cap and not best_desc:
                        best_desc = cap
            if not best_desc and e.get("summary") and not str(e.get("summary")).startswith("自动入库资产 "):
                best_desc = str(e.get("summary"))

        if not best_desc:
            best_desc = (
                pmeta.get("reject_reason")
                or pmeta.get("note")
                or (f"🪄 {best_prompt[:80]}" if best_prompt else "")
                or f"{info[category_icon]} {info[module_title]} · {Path(rel_path).name}"
            )
        if not role:
            role = "approved"
        info["role"] = role
        info["description"] = best_desc
        info["prompt"] = best_prompt
        if score_val is not None:
            info["score"] = score_val

        abs_p = root / rel_path
        if abs_p.is_file():
            info["updated_at"] = datetime.fromtimestamp(abs_p.stat().st_mtime, tz=cst).strftime("%Y-%m-%d %H:%M")
        else:
            info["updated_at"] = ""

    # Category summary for Gallery overview
    category_summary: dict[str, dict[str, Any]] = {}
    for ck in list(categories.keys()):
        cm = categories[ck]
        cat_assets = [a for a in assets_info.values() if a.get("category") == ck]
        cat_mods = [m for m, mc in modules.items() if mc.get("category") == ck]
        if not cat_assets and not cat_mods and ck in ("anim", "misc"):
            continue
        category_summary[ck] = {
            "key": ck,
            "label": cm.get("label", ck),
            "short": cm.get("short") or str(cm.get("label", ck)).split(" (")[0],
            "icon": cm.get("icon", "📦"),
            "total_assets": len(cat_assets),
            "approved_count": sum(1 for a in cat_assets if a.get("role") in ("anchor", "approved")),
            "rejected_count": sum(1 for a in cat_assets if a.get("role") in ("rejected", "draft_violation")),
            "module_count": len(cat_mods),
        }

    # Load Taste, Two-Layer Knowledge Cards (Private + Shared) & Reflections for Atlas display
    profile_data: dict[str, Any] = {
        "taste": {},
        "knowledge_cards": [],
        "private_knowledge_cards": [],
        "shared_knowledge_cards": [],
        "shared_dir": "",
        "reflections": [],
        "converge_latest": None,
    }
    taste_f = mem_dir / "_profile" / "taste.json"
    if taste_f.is_file():
        try:
            profile_data["taste"] = json.loads(taste_f.read_text(encoding="utf-8"))
        except Exception:
            pass
    priv_cards_list: list[dict[str, Any]] = []
    know_f = mem_dir / "_knowledge" / "index.json"
    if know_f.is_file():
        try:
            kd = json.loads(know_f.read_text(encoding="utf-8"))
            for c in (kd.get("cards") or {}).values():
                if isinstance(c, dict):
                    cc = dict(c)
                    cc["layer_scope"] = "private"
                    cc["project_id"] = active_pid
                    cc["project_name"] = active_pname
                    priv_cards_list.append(cc)
        except Exception:
            pass
    shared_cards_list: list[dict[str, Any]] = []
    try:
        from improve import load_shared_knowledge_index, shared_knowledge_dir
        profile_data["shared_dir"] = str(shared_knowledge_dir(root))
        sd = load_shared_knowledge_index(root, auto_seed=True)
        for c in (sd.get("cards") or {}).values():
            if isinstance(c, dict):
                cc = dict(c)
                cc["layer_scope"] = "shared"
                cc.setdefault("project_id", "global_shared")
                cc.setdefault("project_name", "全局共享通用库 (Global Shared)")
                shared_cards_list.append(cc)
    except Exception:
        pass
    profile_data["private_knowledge_cards"] = priv_cards_list
    profile_data["shared_knowledge_cards"] = shared_cards_list
    priv_ids = {c.get("id") for c in priv_cards_list if c.get("id")}
    profile_data["knowledge_cards"] = priv_cards_list + [c for c in shared_cards_list if c.get("id") not in priv_ids]
    refl_d = mem_dir / "_reflections"
    if refl_d.is_dir():
        for rf in sorted(refl_d.glob("*.json"), key=lambda x: x.name, reverse=True)[:10]:
            try:
                profile_data["reflections"].append(json.loads(rf.read_text(encoding="utf-8")))
            except Exception:
                pass
    conv_f = mem_dir / "converge" / "latest.json"
    if conv_f.is_file():
        try:
            profile_data["converge_latest"] = json.loads(conv_f.read_text(encoding="utf-8"))
        except Exception:
            pass

    project_libraries = _load_all_project_libraries(root, active_meta, assets_info)

    built_at = datetime.now(cst).strftime("%Y-%m-%d %H:%M:%S UTC+8")
    sig_src = json.dumps({
        "p": active_pid,
        "pl": [(pl.get("project_id"), pl.get("entries_count"), len(pl.get("knowledge_cards") or [])) for pl in project_libraries],
        "a": [(k, v.get("sha256_16"), v.get("description"), v.get("role"), v.get("module")) for k, v in sorted(assets_info.items())],
        "e": [(e.get("id"), e.get("summary"), e.get("status"), e.get("stale")) for e in entries],
        "m": list(modules.keys()),
        "t": profile_data["taste"].get("updated_at", ""),
        "k": len(profile_data["knowledge_cards"]),
        "r": len(profile_data["reflections"]),
    }, ensure_ascii=False, sort_keys=True)
    build_id = hashlib.sha256(sig_src.encode("utf-8")).hexdigest()[:16]

    return {
        "root": str(root),
        "built_at": built_at,
        "build_id": build_id,
        "active_project": active_meta,
        "project_libraries": project_libraries,
        "config": config,
        "categories": categories,
        "category_summary": category_summary,
        "modules": modules,
        "synonyms": synonyms,
        "entries": entries,
        "specs": specs,
        "workflows": workflows,
        "assets": assets_info,
        "qa_issues": qa_issues,
        "stale_entries": stale_entries,
        "profile": profile_data,
    }


def refresh_atlas_silent(root: Path, out_name: str = "art-atlas.html") -> Path | None:
    """Automatically regenerate art-atlas.html and .memory-art/atlas_ping.js after any write op."""
    try:
        from build_atlas import generate_atlas_html
        fresh_data = load_project(root)
        out_file = root / out_name
        generate_atlas_html(fresh_data, out_file)
        return out_file
    except Exception:
        return None

def cmd_list(data: dict[str, Any]) -> int:
    print(f"🎨 {data['config'].get('project', {}).get('name', 'pmem-art')} · 美术模块与资产总览\n")
    print(f"{'模块 ID':<28} {'模块名称':<22} {'记忆数':<8} {'图片资产':<8} {'红线数':<8} {'状态'}")
    print("-" * 92)
    for mod_id, mod_cfg in data["modules"].items():
        mod_entries = [e for e in data["entries"] if e.get("module") == mod_id]
        mod_assets = [a for a in data["assets"].values() if a.get("module") == mod_id]
        redlines = [e for e in mod_entries if e.get("kind") == "style_redline"]
        has_issue = any(not a["qa_passed"] for a in mod_assets) or any(e["stale"] for e in mod_entries)
        status_str = "⚠️ 需复核/修复" if has_issue else "✅ 健康"
        print(f"{mod_id:<28} {mod_cfg.get('title', '')[:20]:<22} {len(mod_entries):<8} {len(mod_assets):<8} {len(redlines):<8} {status_str}")
    return 0

def cmd_search(data: dict[str, Any], module: str, path: str, query: str) -> int:
    target_mod = module
    if not target_mod and path:
        for mod_id, mod_cfg in data["modules"].items():
            for pat in mod_cfg.get("paths", []):
                if fnmatch.fnmatch(path, pat):
                    target_mod = mod_id
                    break
    # Include parent module lessons & project-wide lessons (just like mry-ship/pmem!)
    parent_mod = data["modules"].get(target_mod, {}).get("parent") or (
        ".".join(target_mod.split(".")[:-1]) if "." in target_mod and ".".join(target_mod.split(".")[:-1]) in data["modules"] else None
    )
    matched = []
    for e in data["entries"]:
        em = e.get("module", "")
        if target_mod and em not in (target_mod, parent_mod) and e.get("scope") != "project":
            continue
        if query:
            hay = json.dumps(e, ensure_ascii=False).lower()
            if query.lower() not in hay:
                continue
        matched.append(e)
    from improve import rank_memory_entry
    matched.sort(
        key=lambda x: rank_memory_entry(x, target_module=target_mod or "", query=query or "", prioritize_kind=True),
        reverse=True,
    )

    mod_cfg = data["modules"].get(target_mod, {})
    result = {
        "ok": True,
        "server": "pmem-art",
        "queried_module": target_mod or "ALL",
        "parent_module_inherited": parent_mod,
        "module_specs": mod_cfg.get("specs", {}),
        "module_palette": mod_cfg.get("palette", []),
        "lessons": [
            {
                "id": e["id"],
                "module": e["module"],
                "kind": e["kind"],
                "kind_label": e["kind_label"],
                "entity": e.get("entity"),
                "scope": e.get("scope", "module"),
                "stale": e["stale"],
                "stale_reasons": e["stale_reasons"],
                "summary": e.get("summary"),
                "verify": e.get("verify"),
                "applies": e.get("applies"),
                "ai_params": e.get("ai_params"),
                "assets": e.get("assets"),
                "content": e.get("body"),
            }
            for e in matched if e["layer"] == "lesson"
        ],
        "asset_records_and_plans": [
            {
                "id": e["id"],
                "module": e["module"],
                "kind": e["kind"],
                "kind_label": e["kind_label"],
                "summary": e.get("summary"),
                "specs": e.get("specs"),
                "assets": [a.get("path") for a in (e.get("assets") or []) if isinstance(a, dict)],
            }
            for e in matched if e["layer"] == "record"
        ],
        "layered_knowledge": (lambda: (
            __import__("improve").recall_layered_knowledge_cards(
                Path(data.get("root", ".")),
                target_module=target_mod or "",
                query=query or "",
                limit=6,
            )
        ))(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

def cmd_validate(data: dict[str, Any]) -> int:
    print("🔍 pmem-art 资产管线规范与视觉锚点过期（Stale）自动质检报告\n")
    for path, info in data["assets"].items():
        badge = "✅ PASS" if info["qa_passed"] else "❌ FAIL"
        print(f"  {badge}  {path:<52} [{info.get('resolution', '?'):<9} | {info.get('mode', '?'):<4} | {info.get('size_kb', 0):>5} KB | {info['module']}]")
        for iss in info["qa_issues"]:
            print(f"         ↳ ⚠️ 违规项: {iss}")
    print("\n📌 记忆条目过期核对（Stale Check）：")
    if not data["stale_entries"]:
        print("  ✅ 所有美术记忆条目的关联图片哈希与规格均匹配，无过期条目。")
    else:
        for se in data["stale_entries"]:
            print(f"  ⚠️ STALE  [{se['id']}] ({se['module']}) {se['summary']}")
            for r in se["reasons"]:
                print(f"         ↳ 原因: {r}")
    return 0 if not data["qa_issues"] else 1

def cmd_hook(root: Path, data: dict[str, Any], event: str) -> int:
    """Cursor / Claude Code hooks：生图前召回记忆；落盘后轻量提示；不阻断对话。"""
    payload: dict[str, Any] = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
    except Exception:
        payload = {}

    tool = str(payload.get("toolName") or payload.get("tool") or "")
    # 尝试从常见字段抠出路径 / prompt / 用户话
    user_msg = str(payload.get("user_message") or payload.get("message") or "")
    prompt = ""
    path = ""
    args_obj = payload.get("arguments") or payload.get("args") or {}
    if isinstance(args_obj, dict):
        prompt = str(args_obj.get("prompt") or args_obj.get("description") or "")
        path = str(args_obj.get("path") or args_obj.get("file") or args_obj.get("outputPath") or "")
    if not prompt and user_msg:
        prompt = user_msg

    advice: list[str] = []
    # 生图前 / 写资产前：自动 search 相关记忆
    if event in ("pre-tool", "pre-gen") or (event == "pre-tool" and re.search(r"GenerateImage|image|Write|Edit", tool, re.I)):
        # 推断模块
        module = ""
        q = prompt or user_msg or path
        if q:
            from feedback import infer_module_from_text
            module = infer_module_from_text(q, data)
        matched = []
        if module:
            matched = [e for e in data.get("entries") or [] if e.get("module") == module or str(e.get("module", "")).startswith(module.split(".")[0])]
            # 优先红线与定稿 + 最简加权（精确模块 > 胜出评分 > 关键词重叠 > 日期）
            from improve import rank_memory_entry
            matched = sorted(
                matched,
                key=lambda e: (
                    -{"style_redline": 0, "recipe": 1, "art_decision": 2, "visual_correction": 3}.get(e.get("kind"), 9),
                    *rank_memory_entry(e, target_module=module, query=q),
                ),
                reverse=True,
            )[:6]
        from improve import recall_layered_knowledge_cards
        layered_k = recall_layered_knowledge_cards(root, target_module=module, query=q, limit=4)
        if matched or layered_k:
            advice.append(
                f"🎨 pmem-art 双层记忆召回 · 模块 {module or '?'}（私有条目 {len(matched)} 条 + 知识卡 {len(layered_k)} 张）"
            )
            for e in matched:
                advice.append(f"  · [private:{e.get('kind')}] {e.get('summary', '')[:100]}")
            for kc in layered_k:
                advice.append(f"  · [{kc.get('layer_scope', 'shared')}:knowledge] {kc.get('title')}: {kc.get('body', '')[:80]}")
        elif q:
            advice.append(f"🎨 pmem-art：模块 {module or '未识别'} 暂无私有记忆，生图后请用自然语言反馈沉淀（如「太赛博」「这版留着」）。")

    if event in ("post-tool", "post-asset"):
        advice.append("💬 若这张不对/要留着：直接说「太赛博 / 头太大 / 这版留着 / 换成水彩」，我会写入 pmem-art 记忆。")
        # 若落盘路径像图片，提示 ingest
        if path and re.search(r"\.(png|jpe?g|webp)$", path, re.I):
            advice.append(f'📥 可选归档：python3 pmem_art.py ingest {path} -p "{(prompt or "")[:80]}" --apply')

    if event == "stop":
        advice.append("🧠 pmem-art：本轮若有审美拍板，记得一句话留下（「以后都用这色板」「别再画霓虹」）。")

    # Cursor hook 协议：输出 JSON，附加 agentMessage 提示（兼容 continue）
    out = {
        "continue": True,
        "server": "pmem-art",
        "version": VERSION,
        "event": event,
        "agentMessage": "\n".join(advice) if advice else "",
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0



def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pmem-art",
        description="Cursor 对话驱动的个人美术积累记忆：反馈沉淀 → 下次生图更准（classify/domains 在后端默默工作）",
    )
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--version", action="version", version=f"pmem-art {VERSION}")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Mode A：空项目冷启动 — 写入 scaffold 分类、空 assets 目录、gate=warn")
    p_init.add_argument("--name", default="Untitled Art Project", help="项目名称")
    p_init.add_argument("--force", action="store_true", help="允许在已有 .memory-art 上重写 config/modules 脚手架（保留 entries）")

    p_boot = sub.add_parser("bootstrap", help="Mode A/B：young 脚手架确认 或 legacy 扫描乱资产并只提议不移动")
    p_boot.add_argument("--mode", choices=("young", "legacy"), required=True)
    p_boot.add_argument("--auto-accept-depth", type=int, default=2, help="前 N 层路径可自动升为模块（仍需 --apply 才写入）")
    p_boot.add_argument("--roots", nargs="*", default=None, help="额外资产扫描根，如 Art Content Assets/Art")
    p_boot.add_argument("--apply", action="store_true", help="确认执行：按 depth 提升候选；legacy 仍不移动文件")

    p_sync = sub.add_parser("sync", help="Mode C：扫描新文件夹 → 更新 candidates（可选按 depth 自动 accept）")
    p_sync.add_argument("--auto-accept-depth", type=int, default=None)
    p_sync.add_argument("--apply", action="store_true", help="对 depth 内高置信候选直接提升为 active")

    sub.add_parser("candidates", help="列出 sync/bootstrap 提出的待确认候选模块")

    p_accept = sub.add_parser("accept", help="将 candidate/scaffold 提升为 active（一次确认）")
    p_accept.add_argument("module_id", nargs="?", default="")
    p_accept.add_argument("--all", action="store_true", help="接受全部候选（及已有文件的 scaffold）")

    p_place = sub.add_parser("place", help="把文件规划/移动到模块规范路径（默认 dry-run；--apply 才改磁盘）")
    p_place.add_argument("src", nargs="?", default="", help="源文件路径")
    p_place.add_argument("--module", default="", help="目标模块；省略则按路径推断")
    p_place.add_argument("--role", default="approved", help="资产角色：anchor/approved/rejected/reference")
    p_place.add_argument("--apply", action="store_true", help="真正执行 move（默认只打印计划）")
    p_place.add_argument("--plan-orphans", action="store_true", help="为所有未映射孤儿资产生成归位计划")

    p_classify = sub.add_parser("classify", help="多信号自动分类：路径+Prompt+图像特征+已有模块 → 建议 module 与置信度")
    p_classify.add_argument("path", nargs="?", default="", help="图片路径（可省略，仅按 prompt 分类）")
    p_classify.add_argument("--prompt", "-p", default="", help="用户或 Agent 生图提示词 / 说明")
    p_classify.add_argument("--json-prompt", default="", help="从 JSON 文件读取 prompt 字段")

    p_ingest = sub.add_parser("ingest", help="classify → 自动扩展模块 → 归位 assets/<domain>/...（默认 dry-run）")
    p_ingest.add_argument("path", help="待入库图片路径")
    p_ingest.add_argument("--prompt", "-p", default="", help="生图 Prompt / 用途说明（强烈建议传入）")
    p_ingest.add_argument("--apply", action="store_true", help="执行移动并写入模块；年轻项目也可设 bootstrap.auto_place: true")
    p_ingest.add_argument("--no-record", action="store_true", help="不自动写 asset_record 桩")

    p_cwatch = sub.add_parser("classify-watch", help="扫描 watch_dirs 中未映射图片并 classify；--apply 对高置信度自动 ingest")
    p_cwatch.add_argument("--apply", action="store_true")

    sub.add_parser("list", help="列出所有美术模块、资产数与健康状态")
    p_search = sub.add_parser("search", help="按模块/路径/关键词检索美术记忆（含红线、色板、规格与 AI 配方）")
    p_search.add_argument("query", nargs="?", default="")
    p_search.add_argument("--module", "-m", default="")
    p_search.add_argument("--path", default="")

    sub.add_parser("validate", help="校验所有图片资产的分辨率、RGBA 透明通道、安全边距与记忆 Stale 状态")
    sub.add_parser("doctor", help="覆盖率%% / 孤儿 / 多风格冲突 / 生命周期体检 + 资产质检")
    p_atlas = sub.add_parser("atlas", help="生成/更新自包含可视化美术记忆图谱工作台 HTML (art-atlas.html)")
    p_atlas.add_argument("--out", default="art-atlas.html")

    p_fb = sub.add_parser("feedback", help="把画师自然语言反馈沉淀为记忆（太赛博/头太大/这版留着/换成水彩…）")
    p_fb.add_argument("text", nargs="?", default="", help="画师原话；也可 --text")
    p_fb.add_argument("--text", dest="text_opt", default="", help="画师原话（与位置参数二选一）")
    p_fb.add_argument("--module", "-m", default="", help="目标模块；省略则从原文推断")
    p_fb.add_argument("--asset", "-a", default="", help="关联图片路径（正例/反例）")
    p_fb.add_argument("--kind", default="", help="强制记忆类型；默认自动判定")
    p_fb.add_argument("--dry-run", action="store_true", help="只打印判定，不写文件")
    p_fb.add_argument("--verbose", "-v", action="store_true", help="详细输出（默认一行小提示）")
    p_fb.add_argument("--silent", action="store_true", default=True, help="静默（默认）")

    p_note = sub.add_parser("note", help="feedback 的别名（更短）")
    p_note.add_argument("text", nargs="?", default="")
    p_note.add_argument("--text", dest="text_opt", default="")
    p_note.add_argument("--module", "-m", default="")
    p_note.add_argument("--asset", "-a", default="")
    p_note.add_argument("--kind", default="")
    p_note.add_argument("--dry-run", action="store_true")
    p_note.add_argument("--verbose", "-v", action="store_true")
    p_note.add_argument("--silent", action="store_true", default=True)

    p_skills = sub.add_parser("skills", help="安装/刷新或列出内置的 Cursor / Claude Code / Codex 美术技能 (/pmem-draw 等)")
    p_skills.add_argument("--install", action="store_true", help="安装或刷新全部技能文件到 .cursor / .claude / .agents")
    p_skills.add_argument("--list", action="store_true", help="列出所有内置美术技能与触发方式")

    p_conv = sub.add_parser("converge", help="闭环自评收敛（Warm-Start + quality/fast · 最多8轮 ≥9.5 · 反思）")
    p_conv.add_argument("action", choices=("start", "round", "finish", "table", "status", "warm"), help="子操作")
    p_conv.add_argument("--session", default="latest", help="会话 ID（默认 latest）")
    p_conv.add_argument("--goal", "-g", default="", help="本次生图目标描述")
    p_conv.add_argument("--module", "-m", default="", help="目标模块 ID")
    p_conv.add_argument("--ref-image", default="", help="垫图/参考图路径（若有）")
    p_conv.add_argument("--ref-analysis", default="", help="参考图视觉解构结论摘要")
    p_conv.add_argument("--threshold", type=float, default=9.5, help="合格分数线（默认 9.5）")
    p_conv.add_argument("--max-rounds", type=int, default=8, help="最大收敛轮次（默认 8）")
    p_conv.add_argument("--mode", dest="converge_mode", choices=("quality", "fast"), default="quality",
                        help="quality=完整8×9.5（默认）；fast=warm-start 置信高时可 fast-track")
    p_conv.add_argument("--draft", action="store_true", help="用户明确要草稿/fast 时允许软合格线（仅 fast 模式）")
    p_conv.add_argument("--round", dest="round_num", type=int, default=0, help="当前轮次序号 (1..8)")
    p_conv.add_argument("--image", "-i", default="", help="本轮生成图片路径")
    p_conv.add_argument("--score", "-s", type=float, default=0.0, help="本轮综合评分（满分 10.0）")
    p_conv.add_argument("--dims", default="", help="五维细分得分说明")
    p_conv.add_argument("--strengths", default="", help="本轮合理/亮点之处")
    p_conv.add_argument("--defects", default="", help="本轮不合理/缺陷之处")
    p_conv.add_argument("--next-fix", default="", help="下一轮叠加修正策略")
    p_conv.add_argument("--prompt", "-p", default="", help="本轮使用的 Prompt")
    p_conv.add_argument("--apply", action="store_true", help="finish 时自动将胜出图与踩坑红线写入 .memory-art")
    p_conv.add_argument("--no-apply", action="store_true", help="finish 时仅打印表格不写入记忆")
    p_conv.add_argument("--verbose", "-v", action="store_true", help="打印全量 Markdown 报告（默认静默：一行结论+小提示）")
    p_conv.add_argument("--silent", action="store_true", default=True, help="静默自动驾驶（默认开启）")
    p_conv.add_argument("--no-silent", action="store_true", help="关闭静默，等同 --verbose 的报告倾倒")

    p_improve = sub.add_parser("improve", help="自我迭代：扫描反思+反馈 → 更新口味档案（/pmem-improve）")
    p_improve.add_argument("action", nargs="?", default="run", choices=("run", "progress", "reflect"), help="run|progress")
    p_improve.add_argument("--last", type=int, default=20, help="扫描最近 N 份反思")
    p_improve.add_argument("--dry-run", action="store_true", help="只报告不写档案")
    p_improve.add_argument("--silent", action="store_true", help="静默模式（一行小提示）")
    p_improve.add_argument("--verbose", "-v", action="store_true", help="完整报告（默认；显式 peek）")

    sub.add_parser("progress", help="进步曲线：近7/30胜出分、轮次、能力短板趋势、知识广度")

    p_taste = sub.add_parser("taste", help="个人口味档案 show|update")
    p_taste.add_argument("action", choices=("show", "update"), help="show|update")
    p_taste.add_argument("--key", default="", help="update 时的字段名")
    p_taste.add_argument("--value", default="", help="update 时追加的值")

    p_coach = sub.add_parser("coach", help="能力教练：短板→练习→下一张目标（/pmem-coach）")
    p_coach.add_argument("--last", type=int, default=20, help="扫描最近 N 份反思")

    p_learn = sub.add_parser("learn", help="双层知识广度扩展 suggest|accept|list|promote（/pmem-learn）")
    p_learn.add_argument("action", nargs="?", default="suggest", choices=("suggest", "accept", "list", "propose", "promote"), help="子操作")
    p_learn.add_argument("--limit", type=int, default=5, help="建议条数")
    p_learn.add_argument("--all", dest="accept_all", action="store_true", help="accept 全部建议")
    p_learn.add_argument("--ids", default="", help="accept 指定 id，逗号分隔")
    p_learn.add_argument("--seed-modules", action="store_true", help="接受时写入可选空模块种子")
    p_learn.add_argument("--silent", action="store_true", help="只写提案不打印（后台用）")

    p_hook = sub.add_parser("hook", help="处理 Cursor / Claude Code / Codex 的 Hook 闸门事件")
    p_hook.add_argument("event", choices=("pre-tool", "post-tool", "stop", "pre-gen", "post-asset"))

    args = parser.parse_args()
    root = Path(args.root).resolve()

    # Commands that must work before .memory-art exists
    if args.command == "init":
        from lifecycle import cmd_init
        return cmd_init(root, project_name=args.name, force=args.force)
    if args.command == "skills":
        from skills_kit import install_skills_and_agent_configs, SKILL_SPECS
        if args.list and not args.install:
            print("🎨 pmem-art 内置美术技能列表（Cursor / Claude Code / Codex 通用）：\n")
            for sp in SKILL_SPECS:
                print(f"  /{sp['name']:<16} (别名 /{sp['alias']:<11}) — {sp['title']}")
                print(f"     ↳ {sp['description']}\n")
            return 0
        install_skills_and_agent_configs(root, quiet=False)
        return 0

    # Soft-load when memory missing (bootstrap/legacy on half-empty trees)
    mem = root / MEMORY_DIR
    if not mem.exists() and args.command in ("bootstrap", "sync"):
        from lifecycle import cmd_init
        print("ℹ️  未检测到 .memory-art，先执行隐式 init 脚手架…")
        cmd_init(root, project_name=root.name)

    data = load_project(root)
    # Normalize missing status → active (demo / mature projects)
    for mid, cfg in (data.get("modules") or {}).items():
        if isinstance(cfg, dict) and "status" not in cfg:
            cfg["status"] = "active"

    if args.command == "bootstrap":
        from lifecycle import cmd_bootstrap
        return cmd_bootstrap(
            root, data, mode=args.mode,
            auto_accept_depth=args.auto_accept_depth,
            apply=args.apply, roots=args.roots,
        )
    if args.command == "sync":
        from lifecycle import cmd_sync
        return cmd_sync(root, data, auto_accept_depth=args.auto_accept_depth, apply_accept=args.apply)
    if args.command == "candidates":
        from lifecycle import cmd_candidates
        return cmd_candidates(root)
    if args.command == "accept":
        from lifecycle import cmd_accept
        return cmd_accept(root, data, module_id=args.module_id, accept_all=args.all)
    if args.command == "place":
        from lifecycle import cmd_place
        return cmd_place(
            root, data, src=args.src, module=args.module, role=args.role,
            apply=args.apply, plan_all_orphans=args.plan_orphans,
        )
    if args.command == "classify":
        from classify import cmd_classify
        prompt = args.prompt
        if args.json_prompt:
            import json as _json
            prompt = _json.loads(Path(args.json_prompt).read_text(encoding="utf-8")).get("prompt", prompt)
        return cmd_classify(root, data, path=args.path, prompt=prompt)
    if args.command == "ingest":
        from classify import cmd_ingest
        return cmd_ingest(
            root, data, path=args.path, prompt=args.prompt,
            apply=args.apply, seed_record=not args.no_record,
        )
    if args.command == "classify-watch":
        from classify import cmd_watch_sync_classify
        return cmd_watch_sync_classify(root, data, apply=args.apply)
    if args.command in (None, "list"):
        return cmd_list(data)
    if args.command == "search":
        return cmd_search(data, args.module, args.path, args.query)
    if args.command == "validate":
        return cmd_validate(data)
    if args.command == "doctor":
        from lifecycle import cmd_doctor_lifecycle
        rc1 = cmd_doctor_lifecycle(root, data)
        print()
        rc2 = cmd_validate(data)
        return rc1 or rc2
    if args.command == "atlas":
        from build_atlas import generate_atlas_html
        out_file = root / args.out
        generate_atlas_html(data, out_file)
        print(f"✨ 已生成可视化美术记忆图谱工作台: {out_file} ({round(out_file.stat().st_size / 1024, 1)} KB)")
        return 0
    if args.command in ("feedback", "note"):
        from feedback import cmd_feedback
        raw = (getattr(args, "text_opt", "") or "") or (getattr(args, "text", "") or "")
        return cmd_feedback(
            root, data, text=raw, module=args.module, asset=args.asset,
            kind=args.kind, apply=not args.dry_run,
            silent=not bool(getattr(args, "verbose", False)),
            verbose=bool(getattr(args, "verbose", False)),
        )
    if args.command == "converge":
        from skills_kit import cmd_converge
        return cmd_converge(
            root,
            data,
            args.action,
            session_id=args.session,
            goal=args.goal,
            module=args.module,
            ref_image=args.ref_image,
            ref_analysis=args.ref_analysis,
            threshold=args.threshold,
            max_rounds=args.max_rounds,
            round_num=args.round_num,
            image=args.image,
            score=args.score,
            dims=args.dims,
            strengths=args.strengths,
            defects=args.defects,
            next_fix=args.next_fix,
            prompt=args.prompt,
            apply_memory=(not args.no_apply),
            converge_mode=getattr(args, "converge_mode", "quality") or "quality",
            draft_ok=bool(getattr(args, "draft", False)),
            verbose=bool(getattr(args, "verbose", False) or getattr(args, "no_silent", False)),
            silent=not bool(getattr(args, "verbose", False) or getattr(args, "no_silent", False)),
        )
    if args.command == "improve":
        from improve import cmd_improve
        return cmd_improve(
            root, data, action=args.action or "run",
            last_n=args.last, apply=not args.dry_run,
            silent=bool(getattr(args, "silent", False)) and not bool(getattr(args, "verbose", False)),
        )
    if args.command == "progress":
        from improve import cmd_progress
        return cmd_progress(root, data)
    if args.command == "taste":
        from improve import cmd_taste
        return cmd_taste(root, data, action=args.action, key=args.key, value=args.value)
    if args.command == "coach":
        from improve import cmd_coach
        return cmd_coach(root, data, last_n=args.last)
    if args.command == "learn":
        from improve import cmd_learn
        ids = [x.strip() for x in (args.ids or "").split(",") if x.strip()] or None
        return cmd_learn(
            root, data, action=args.action or "suggest",
            limit=args.limit, accept_all=args.accept_all,
            seed_modules=args.seed_modules, ids=ids,
            silent=bool(getattr(args, "silent", False)),
        )
    if args.command == "hook":
        return cmd_hook(root, data, args.event)
    parser.print_help()
    return 0

def _cli_entry() -> int:
    rc = main()
    try:
        if len(sys.argv) > 1 and sys.argv[1] in (
            "init", "bootstrap", "sync", "accept", "place",
            "ingest", "classify-watch", "feedback", "note",
            "converge", "improve", "taste", "learn", "hook",
        ):
            p = argparse.ArgumentParser(add_help=False)
            p.add_argument("--root", default=".")
            known, _ = p.parse_known_args()
            root_p = Path(known.root).resolve()
            if (root_p / MEMORY_DIR).is_dir():
                refresh_atlas_silent(root_p)
    except Exception:
        pass
    return rc

if __name__ == "__main__":
    raise SystemExit(_cli_entry())
