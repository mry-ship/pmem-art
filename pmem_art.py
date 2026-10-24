#!/usr/bin/env python3
"""
pmem-art: 面向游戏/影视美术团队与 AI 美术 Agent 的插拔式视觉记忆、资产管线质检与可视化图谱系统
基于 mry-ship/pmem 架构针对美术生产流（2D立绘/三视图/表情差分/场景光照/UI九宫格/VFX序列帧/ComfyUI配方）深度演化。
零第三方强依赖（仅使用 Python 3.10+ 标准库；若安装 PyYAML 则优先使用，否则使用内置解析器）。
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

VERSION = "0.7.0-art"
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

def load_project(root: Path) -> dict[str, Any]:
    mem_dir = root / MEMORY_DIR
    config = load_yaml((mem_dir / "config.yaml").read_text(encoding="utf-8")) if (mem_dir / "config.yaml").exists() else {}
    modules_doc = load_yaml((mem_dir / "modules.yaml").read_text(encoding="utf-8")) if (mem_dir / "modules.yaml").exists() else {}
    categories = modules_doc.get("categories", {})
    modules = modules_doc.get("modules", {})
    synonyms = modules_doc.get("synonyms", [])

    # Load entries
    entries: list[dict[str, Any]] = []
    entries_dir = mem_dir / "entries"
    if entries_dir.is_dir():
        for md_file in sorted(entries_dir.rglob("*.md")):
            raw = md_file.read_text(encoding="utf-8")
            m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", raw, re.DOTALL)
            if not m:
                continue
            meta = load_yaml(m.group(1))
            body = m.group(2).strip()
            meta["body"] = body
            meta["file_path"] = str(md_file.relative_to(root))
            k_info = KIND_META.get(meta.get("kind", ""), {"label": meta.get("kind", ""), "layer": "lesson", "badge": "info", "order": 9})
            meta["kind_label"] = k_info["label"]
            meta["layer"] = k_info["layer"]
            meta["badge"] = k_info["badge"]
            meta["kind_order"] = k_info["order"]
            entries.append(meta)

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

    return {
        "root": str(root),
        "config": config,
        "categories": categories,
        "modules": modules,
        "synonyms": synonyms,
        "entries": entries,
        "specs": specs,
        "workflows": workflows,
        "assets": assets_info,
        "qa_issues": qa_issues,
        "stale_entries": stale_entries,
    }

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
    matched.sort(key=lambda x: x.get("kind_order", 9))

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

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pmem-art",
        description="挂载式美术记忆系统：冷启动脚手架 / 老项目扫描接入 / 持续 sync→accept→闸门循环",
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
    p_search.add_argument("--module", default="")
    p_search.add_argument("--path", default="")

    sub.add_parser("validate", help="校验所有图片资产的分辨率、RGBA 透明通道、安全边距与记忆 Stale 状态")
    sub.add_parser("doctor", help="覆盖率%% / 孤儿 / 多风格冲突 / 生命周期体检 + 资产质检")
    p_atlas = sub.add_parser("atlas", help="生成/更新自包含可视化美术记忆图谱工作台 HTML (art-atlas.html)")
    p_atlas.add_argument("--out", default="art-atlas.html")

    p_hook = sub.add_parser("hook", help="处理 Cursor / Claude Code / Codex 的 Hook 闸门事件")
    p_hook.add_argument("event", choices=("pre-tool", "post-tool", "stop"))

    args = parser.parse_args()
    root = Path(args.root).resolve()

    # Commands that must work before .memory-art exists
    if args.command == "init":
        from lifecycle import cmd_init
        return cmd_init(root, project_name=args.name, force=args.force)

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
    if args.command == "hook":
        print(json.dumps({"continue": True, "server": "pmem-art", "version": VERSION}))
        return 0
    parser.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
