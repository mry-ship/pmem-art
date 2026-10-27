#!/usr/bin/env python3
"""
pmem-art: 画师在 Cursor 里越画越准的个人美术积累记忆。

心智模型（不是审稿台 / 不是 CLI 流水线）：
  生图 → 你用自然语言说「哪里不对 / 这版留着 / 换成水彩」→ 记忆长大 → 下次生图自动召回 → 更准。

classify / ingest / domains 仍在后端默默工作；日常入口是 Cursor 对话 + Skills。
v0.12：评分履历默认可见（`--quiet` 只要终稿）· 记忆写入仍静默 · Warm-Start / coach/learn 进阶 peek。
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

from lifecycle import ensure_stdio_survives_locale

ensure_stdio_survives_locale()

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

_HEX_COLOR_RE = re.compile(r"#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})\b")


def _shield_hex_colors(text: str) -> tuple[str, list[str]]:
    """Keep #RRGGBB / #RRGGBBAA out of YAML comment stripping."""
    found: list[str] = []

    def repl(m: re.Match[str]) -> str:
        found.append(m.group(0))
        return f"__HEX{len(found) - 1}__"

    return _HEX_COLOR_RE.sub(repl, text), found


def _restore_hex(obj: Any, found: list[str]) -> Any:
    if isinstance(obj, str):
        for i, h in enumerate(found):
            obj = obj.replace(f"__HEX{i}__", h)
        return obj
    if isinstance(obj, list):
        return [_restore_hex(x, found) for x in obj]
    if isinstance(obj, dict):
        return {k: _restore_hex(v, found) for k, v in obj.items()}
    return obj


def load_yaml(text: str) -> dict:
    shielded, hexes = _shield_hex_colors(text)
    try:
        import yaml
        data = yaml.safe_load(shielded)
        if isinstance(data, dict):
            return _restore_hex(data, hexes)
    except Exception:
        pass
    lines: list[tuple[int, str]] = []
    for raw_line in shielded.splitlines():
        s = raw_line.rstrip()
        if not s.strip() or s.strip().startswith("#"):
            continue
        # Strip inline comments outside quotes. A '#' is a comment only at
        # line start or after whitespace, and never when it begins a hex color.
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
                    prev = s[i - 1] if i else " "
                    rest = s[i:]
                    is_hex = bool(_HEX_COLOR_RE.match(rest))
                    if (i == 0 or prev.isspace()) and not is_hex:
                        break
                    out_chars.append(ch)
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
    restored = _restore_hex(res, hexes)
    return restored if isinstance(restored, dict) else {}

def _image_mime(path: Path) -> str:
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


def _jpeg_size(raw: bytes) -> tuple[int, int] | None:
    if len(raw) < 4 or raw[:2] != b"\xff\xd8":
        return None
    idx = 2
    n = len(raw)
    while idx + 9 < n:
        if raw[idx] != 0xFF:
            idx += 1
            continue
        marker = raw[idx + 1]
        if marker == 0xFF:
            idx += 1
            continue
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            height, width = struct.unpack(">HH", raw[idx + 5:idx + 9])
            if width > 0 and height > 0:
                return width, height
            return None
        if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
            idx += 2
            continue
        if idx + 4 > n:
            break
        seg_len = struct.unpack(">H", raw[idx + 2:idx + 4])[0]
        if seg_len < 2:
            break
        idx += 2 + seg_len
    return None


def _webp_size(raw: bytes) -> tuple[int, int, bool] | None:
    if len(raw) < 16 or raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        return None
    chunk = raw[12:16]
    if chunk == b"VP8X" and len(raw) >= 30:
        flags = raw[20]
        width = 1 + int.from_bytes(raw[24:27], "little")
        height = 1 + int.from_bytes(raw[27:30], "little")
        return width, height, bool(flags & 0x10)
    if chunk == b"VP8 " and len(raw) >= 30:
        # Lossy bitstream starts after the chunk header; frame tag is 3 bytes then start code.
        start = raw.find(b"\x9d\x01\x2a", 20, 40)
        if start >= 0 and start + 7 <= len(raw):
            width, height = struct.unpack("<HH", raw[start + 3:start + 7])
            return width & 0x3FFF, height & 0x3FFF, False
    if chunk == b"VP8L" and len(raw) >= 25 and raw[20] == 0x2F:
        bits = int.from_bytes(raw[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        alpha = bool((bits >> 28) & 1)
        return width, height, alpha
    return None


def inspect_png(path: Path) -> dict[str, Any]:
    """Read PNG / JPEG / WebP headers for size, mode, and alpha. PNG also keeps tEXt."""
    if not path.is_file():
        return {"exists": False, "path": str(path)}
    raw = path.read_bytes()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    size_kb = round(len(raw) / 1024, 1)
    mime = _image_mime(path)
    b64_uri = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        jpeg = _jpeg_size(raw)
        webp = None if jpeg else _webp_size(raw)
        if jpeg:
            width, height = jpeg
            return {
                "exists": True,
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
                "bit_depth": 8,
                "mode": "RGB",
                "has_alpha": False,
                "size_kb": size_kb,
                "sha256_16": sha16,
                "png_meta": {},
                "data_uri": b64_uri,
            }
        if webp:
            width, height, has_alpha = webp
            return {
                "exists": True,
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
                "bit_depth": 8,
                "mode": "RGBA" if has_alpha else "RGB",
                "has_alpha": has_alpha,
                "size_kb": size_kb,
                "sha256_16": sha16,
                "png_meta": {},
                "data_uri": b64_uri,
            }
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


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _png_corner_samples(raw: bytes) -> dict[str, Any] | None:
    """Sample the four corners of an 8-bit RGB or RGBA PNG. None if this is not a PNG."""
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    width = height = bit_depth = color_type = 0
    idat = b""
    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        chunk_type = raw[pos + 4:pos + 8]
        chunk_data = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR" and len(chunk_data) >= 10:
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk_data[:10])
        elif chunk_type == b"IDAT":
            idat += chunk_data
        elif chunk_type == b"IEND":
            break
    if bit_depth != 8 or color_type not in (2, 6) or not idat or width < 1 or height < 1:
        return {"width": width, "height": height, "sampled": False, "corners": []}
    channels = 4 if color_type == 6 else 3
    stride = width * channels
    try:
        inflated = zlib.decompress(idat)
    except zlib.error:
        return {"width": width, "height": height, "sampled": False, "corners": []}
    if len(inflated) < height * (stride + 1):
        return {"width": width, "height": height, "sampled": False, "corners": []}
    rows: list[bytearray] = []
    i = 0
    prev = bytearray(stride)
    for _y in range(height):
        filt = inflated[i]
        i += 1
        row = bytearray(inflated[i:i + stride])
        i += stride
        if filt == 1:
            for x in range(stride):
                left = row[x - channels] if x >= channels else 0
                row[x] = (row[x] + left) & 255
        elif filt == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif filt == 3:
            for x in range(stride):
                left = row[x - channels] if x >= channels else 0
                row[x] = (row[x] + ((left + prev[x]) // 2)) & 255
        elif filt == 4:
            for x in range(stride):
                a = row[x - channels] if x >= channels else 0
                b = prev[x]
                c = prev[x - channels] if x >= channels else 0
                row[x] = (row[x] + _paeth(a, b, c)) & 255
        elif filt != 0:
            return {"width": width, "height": height, "sampled": False, "corners": []}
        prev = row
        rows.append(row)

    def pix(x: int, y: int) -> tuple[int, int, int, int]:
        o = x * channels
        row = rows[y]
        alpha = row[o + 3] if channels == 4 else 255
        return (row[o], row[o + 1], row[o + 2], alpha)

    corners = [pix(0, 0), pix(width - 1, 0), pix(0, height - 1), pix(width - 1, height - 1)]
    return {"width": width, "height": height, "sampled": True, "corners": corners}


def cmd_ref_read(path: str) -> int:
    """Tell the prompt writer what the reference file actually contains, before any style words are invented."""
    file_path = Path(path)
    if not file_path.is_file():
        print(f"找不到参考图：{path}")
        return 1
    raw = file_path.read_bytes()
    info = inspect_png(file_path)
    print(f"参考图：{file_path.name}")
    if info.get("resolution"):
        print(f"尺寸：{info['resolution']}  模式：{info.get('mode', '未知')}")
    samples = _png_corner_samples(raw) if raw[:8] == b"\x89PNG\r\n\x1a\n" else None
    if samples and samples.get("sampled"):
        corners = samples["corners"]
        clear = sum(1 for _r, _g, _b, a in corners if a < 16)
        if clear >= 3:
            print("底：透明。四角没有颜色。")
            print("提示词里不要写黑底、深底、底板。用一块浅的空底放下物件，这块浅底不是风格。")
        else:
            opaque = [(r, g, b) for r, g, b, a in corners if a >= 200]
            if opaque:
                r = sum(c[0] for c in opaque) // len(opaque)
                g = sum(c[1] for c in opaque) // len(opaque)
                b = sum(c[2] for c in opaque) // len(opaque)
                print(f"底：不透明。四角大约 #{r:02X}{g:02X}{b:02X}。出图用这个底，不要换成别的。")
            else:
                print("底：四角读到了，但不是一整块实底。先看图再写底，不要猜成黑色。")
    elif info.get("mode") == "RGB" and not info.get("has_alpha"):
        print("底：这个文件没有透明通道。先看四角的真实颜色再写底，不要把预览里的黑当成底。")
    else:
        print("底：四角没有读出来。先看图再写底，不要猜成黑色。")
    print("表面：只写眼睛在这张图上看见的那一句。小高光不要写成油亮、光面、发亮。表面光洁，也不要改成毛毡、纸纹或粗颗粒。")
    print("要画别的物件时，不要把这张参考图垫进生图，免得参考图里的物件被画上去。")
    return 0


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
            from lifecycle import iter_md_files
            for md_f in iter_md_files(lib_entries_dir, recursive=True):
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
    raw_modules = modules_doc.get("modules", {}) or {}
    synonyms = modules_doc.get("synonyms", [])
    from lifecycle import MAX_INHERITS_DEPTH, MAX_MODULE_DEPTH, clamp_inherits_parent, clamp_module_id_depth, get_module_parent
    modules: dict[str, Any] = {}
    for r_mid, r_cfg in raw_modules.items():
        c_mid, _ = clamp_module_id_depth(str(r_mid), max_depth=MAX_MODULE_DEPTH, warn=False)
        cfg_d = dict(r_cfg) if isinstance(r_cfg, dict) else {}
        p_val = get_module_parent(cfg_d)
        if p_val:
            c_p, _ = clamp_inherits_parent(c_mid, p_val, raw_modules, max_depth=MAX_INHERITS_DEPTH, warn=False)
            if c_p:
                cfg_d["parent"] = c_p
                cfg_d.setdefault("inherits", c_p)
        modules[c_mid] = cfg_d

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
        from lifecycle import iter_md_files
        for md_file in iter_md_files(entries_dir, recursive=True):
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
        from lifecycle import is_junk_sidecar_name, iter_md_files
        for mod_dir in sorted(specs_dir.iterdir()):
            if not mod_dir.is_dir() or is_junk_sidecar_name(mod_dir.name):
                continue
            specs[mod_dir.name] = {}
            for sf in iter_md_files(mod_dir, recursive=False):
                try:
                    specs[mod_dir.name][sf.stem] = sf.read_text(encoding="utf-8").strip()
                except (UnicodeDecodeError, OSError):
                    continue

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
    asset_exts = {".png", ".jpg", ".jpeg", ".webp"}
    if (root / "assets").is_dir():
        from lifecycle import is_junk_sidecar_name
        for p in sorted((root / "assets").rglob("*")):
            if not p.is_file() or p.suffix.lower() not in asset_exts:
                continue
            rel_parts = p.relative_to(root).parts
            if is_junk_sidecar_name(p.name) or any(is_junk_sidecar_name(part) for part in rel_parts):
                continue
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

    # Paths explicitly marked rejected/draft_violation in entries are intentional
    # counter-examples — still inspect, but do not fail gate / stale on their QA diffs.
    intentional_reject_paths: set[str] = set()
    for e in entries:
        for a in e.get("assets") or []:
            if isinstance(a, dict) and a.get("role") in ("rejected", "draft_violation") and a.get("path"):
                intentional_reject_paths.add(str(a["path"]))

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
            res_ok = (not allowed_res) or (info.get("resolution") in allowed_res)
            if allowed_res and not res_ok:
                issues.append(f"分辨率不符：当前 {info.get('resolution')}，模块要求 {' / '.join(allowed_res)}")
            # Aspect contract only for sizes NOT already on the whitelist
            # (modules like character.Astra allow both 1:1立绘 and 2:1三视图).
            expected_ar = str(mspecs.get("aspect_ratio") or "").strip()
            if expected_ar and (not res_ok) and info.get("width") and info.get("height"):
                try:
                    from skills_kit.image_gates import _aspect_relation
                    ar_rel = _aspect_relation(int(info["width"]), int(info["height"]), expected_ar)
                    if ar_rel.get("hard_fail"):
                        issues.append(
                            f"画幅比例不符：模块要求 aspect_ratio={expected_ar}，"
                            f"实测为 {ar_rel.get('simplified')} ({info.get('resolution')})"
                        )
                except Exception:
                    pass
            if mspecs.get("alpha_required") and not info.get("has_alpha"):
                issues.append(f"缺失透明通道：当前色彩模式为 {info.get('mode')}，模块要求 RGBA 透明通道")
            if mspecs.get("max_size_kb") and info.get("size_kb", 0) > mspecs["max_size_kb"]:
                issues.append(f"文件体积超标：当前 {info.get('size_kb')} KB > 上限 {mspecs['max_size_kb']} KB")
        info["qa_issues"] = issues
        info["qa_intentional_reject"] = rel_path in intentional_reject_paths
        # Intentional rejected samples keep issue text for atlas, but do not fail the gate.
        info["qa_passed"] = (len(issues) == 0) or info["qa_intentional_reject"]
        if issues and not info["qa_intentional_reject"]:
            qa_issues.append({"path": rel_path, "module": mod_id, "issues": issues})

    # Check staleness on entries (compare recorded sha256_16 & QA status of anchored assets)
    stale_entries: list[dict[str, Any]] = []
    for e in entries:
        reasons: list[str] = []
        for a in e.get("assets") or []:
            if not isinstance(a, dict):
                continue
            ap = a.get("path", "")
            role = str(a.get("role") or "")
            expected_sha = a.get("sha256_16")
            actual = assets_info.get(ap, {})
            if role in ("rejected", "draft_violation"):
                # Counter-example drafts: hash drift is expected when regenerating bad samples;
                # pipeline violations are the point of the sample — never mark entry STALE for them.
                a["actual"] = {k: v for k, v in actual.items() if k != "data_uri"}
                continue
            # YAML may parse pure-hex sha as int; coerce before compare/slice.
            exp_s = str(expected_sha) if expected_sha is not None else ""
            act_s = str(actual.get("sha256_16") or "")
            if exp_s and act_s and exp_s != act_s:
                reasons.append(
                    f"关联图片 {ap} 哈希已变更（记录 {exp_s[:8]}… → 当前 {act_s[:8]}…）"
                )
            if actual.get("qa_issues") and not actual.get("qa_intentional_reject"):
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
                            cap = f"✅ {best_prompt} · 自动归类：{info['category_short']} ({mod_id})"
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
                or f"{info['category_icon']} {info['module_title']} · {Path(rel_path).name}"
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
    # Resolve module inheritance chain up to MAX_INHERITS_DEPTH (4 layers, aligned with mry-ship/pmem!)
    from lifecycle import MAX_INHERITS_DEPTH, resolve_module_lineage
    lineage = resolve_module_lineage(target_mod, data["modules"], max_depth=MAX_INHERITS_DEPTH, warn=True) if target_mod else []
    parent_mod = lineage[1] if len(lineage) > 1 else None
    lineage_set = set(lineage)
    matched = []
    for e in data["entries"]:
        # Hide retired lessons so superseded STOP=8.50-style advice cannot resurface.
        if str(e.get("status") or "active").lower() in ("superseded", "archived", "inactive"):
            continue
        em = e.get("module", "")
        if target_mod and em not in lineage_set and e.get("scope") != "project":
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
        "inherits_chain": lineage,
        "max_inherits_depth": MAX_INHERITS_DEPTH,
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
        if info.get("qa_intentional_reject") and info.get("qa_issues"):
            badge = "⚠️ REJECT"
        elif info["qa_passed"]:
            badge = "✅ PASS"
        else:
            badge = "❌ FAIL"
        print(f"  {badge}  {path:<52} [{info.get('resolution', '?'):<9} | {info.get('mode', '?'):<4} | {info.get('size_kb', 0):>5} KB | {info['module']}]")
        for iss in info["qa_issues"]:
            prefix = "反例样张（不计入门禁）" if info.get("qa_intentional_reject") else "违规项"
            print(f"         ↳ ⚠️ {prefix}: {iss}")
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
            def _live(e: dict[str, Any]) -> bool:
                return str(e.get("status") or "active").lower() not in ("superseded", "archived", "inactive")

            matched = [
                e
                for e in data.get("entries") or []
                if _live(e)
                and (
                    e.get("module") == module
                    or str(e.get("module", "")).startswith(module.split(".")[0])
                )
            ]
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

    # 懒巡检：距上次 doctor ≥48h 则后台静默跑；高信号才可能多一行小提示
    try:
        from lifecycle import maybe_lazy_doctor_on_hook
        doctor_tip = maybe_lazy_doctor_on_hook(root, event)
        if doctor_tip:
            advice.append(doctor_tip)
    except Exception as exc:
        # 不阻断 hook；写一行 stderr 便于排障（不进 agentMessage）
        print(f"⚠️ [pmem-art] lazy doctor skipped: {exc}", file=sys.stderr)

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
    p_doctor = sub.add_parser("doctor", help="覆盖率%% / 孤儿 / 多风格冲突 / 生命周期体检 + 资产质检")
    p_doctor.add_argument(
        "--quiet", action="store_true",
        help="静默体检：只写 .memory-art/_profile/last_doctor.json（供 hook 懒巡检）",
    )
    p_doctor.add_argument(
        "--source", default="cli",
        help="写入 last_doctor.source（cli / hook:pre-gen …）",
    )
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

    p_ref = sub.add_parser("ref-read", help="读参考图的底：透明就不要写成黑底；表面词跟看见的走")
    p_ref.add_argument("path", help="参考图路径")

    p_merge = sub.add_parser("merge", help="art-merge 第一段关系机读审 + 阶梯体量审计 + 整梯等分切格")
    p_merge.add_argument(
        "action",
        choices=("relation-judge", "audit", "split-sheet", "normalize", "publish"),
        help="publish=split→audit→(必要时)normalize；其余见 MERGE_PIPELINE.md",
    )
    p_merge.add_argument("--file", "-f", default="", help="merge_phase1_canonical.yaml 路径")
    p_merge.add_argument("--track", "-t", default="", help="tracks 下 id：kitchen | valentine | stationery")
    p_merge.add_argument("--all", action="store_true", help="relation-judge 审全部 track")
    p_merge.add_argument("--dir", "-d", default="", help="audit：方图目录；split-sheet：输出目录")
    p_merge.add_argument("--sheet", default="", help="split-sheet：整梯 16:9 图路径")
    p_merge.add_argument("--phase1", default="", help="audit 时对照 scale_pct")
    p_merge.add_argument("--columns", type=int, default=8, help="split-sheet 列数，默认 8")

    p_skills = sub.add_parser("skills", help="安装/刷新或列出内置的 Cursor / Claude Code / Codex 美术技能 (/pmem-draw 等)")
    p_skills.add_argument("--install", action="store_true", help="安装或刷新全部技能文件到 .cursor / .claude / .agents")
    p_skills.add_argument("--list", action="store_true", help="列出所有内置美术技能与触发方式")

    p_gate = sub.add_parser(
        "check-scale-gates",
        help="出图前验收：肯定锁 grep、recompose 新机位词、high/recompose min_rounds≥2（不调生图）",
    )
    p_gate.add_argument("--scale", default="high", choices=("low", "medium", "high", "recompose"))
    p_gate.add_argument("--goal", default="", help="任务 goal / brief")
    p_gate.add_argument("--prompt", default="", help="拟用生成 prompt（可选）")
    p_gate.add_argument("--best-direction", default="", help="最优方向叠加句（可选）")
    p_gate.add_argument("--recompose-dir", default="", help="recompose 目标机位")
    p_gate.add_argument("--bold", action="store_true", help="按 recompose_bold 大改列检查")
    p_gate.add_argument("--self-check", action="store_true", help="只检查内置四档 directive/hint/min_rounds")

    p_vlm = sub.add_parser(
        "vlm-judge",
        help="独立视觉裁判配置/探测（有 API key 则 converge judge 调真视觉模型；无 key 回退 Agent 自评）",
    )
    p_vlm.add_argument("action", nargs="?", default="status", choices=("status", "probe", "config", "show", "test", "run"))
    p_vlm.add_argument("--image", "-i", default="", help="probe 时要审的图片路径")
    p_vlm.add_argument("--scale", default="medium", choices=("low", "medium", "high", "recompose"))
    p_vlm.add_argument("--goal", default="", help="任务简述（仅作裁判上下文）")
    p_vlm.add_argument("--module", "-m", default="", help="模块 ID")

    p_conv = sub.add_parser("converge", help="闭环收敛（Warm-Start + 严格两步分离：converge generate 仅生图 -> converge judge 独立VLM审图 · 按档位目标阈值动态停机）")
    p_conv.add_argument(
        "action",
        choices=("start", "generate", "judge", "next", "step", "round", "finish", "table", "status", "warm", "lock"),
        help="子操作（next=出图前打印最高分垫图；generate=仅登记生图；judge=独立审图）",
    )
    p_conv.add_argument("--session", "--id", dest="session", default="latest", help="会话 ID（默认 latest，支持 --id 或 --session）")
    p_conv.add_argument("--goal", "--brief", "-g", dest="goal", default="", help="本次生图目标描述（支持 --goal 或 --brief）")
    p_conv.add_argument("--generate-cmd", dest="generate_cmd", default="", help="仅 converge generate 可带的生图命令；judge 阶段传入会被拒绝")
    p_conv.add_argument("--module", "-m", default="", help="目标模块 ID")
    p_conv.add_argument("--ref-image", default="", help="垫图/参考图路径（若有）")
    p_conv.add_argument("--aspect-ratio", dest="aspect_ratio", default="", help="目标画幅比例（如 9:16, 4:3, 3:4；默认跟随参考图比例）")
    p_conv.add_argument("--reference-image-paths", dest="reference_image_paths", default="", help="垫图路径列表（逗号分隔；默认跟随 --ref-image）")
    p_conv.add_argument("--ref-analysis", default="", help="参考图视觉解构结论摘要")
    p_conv.add_argument("--threshold", type=float, default=9.6, help="合格分数线（默认 9.6）")
    p_conv.add_argument("--max-rounds", type=int, default=8, help="最大收敛轮次（默认 8）")
    p_conv.add_argument("--mode", dest="converge_mode", choices=("quality", "fast"), default="quality",
                        help="quality=完整8×9.6（默认）；fast=warm-start 置信高时可 fast-track")
    p_conv.add_argument("--scale", dest="converge_scale", choices=("low", "medium", "high", "recompose"), default="",
                        help="收敛强度：low=只修缺陷，medium=补足加小优化（默认），high=允许重构构图和重做光影，recompose=按用户指定方向改构图")
    p_conv.add_argument("--recompose-dir", dest="recompose_dir", default="",
                        help="当用户明确要求改变构图时指定新构图方向（如：从特写改为全景 / 把主体移到画面左侧三分点）")
    p_conv.add_argument("--draft", action="store_true", help="用户明确要草稿/fast 时允许软合格线（仅 fast 模式）")
    p_conv.add_argument("--round", dest="round_num", type=int, default=0, help="当前轮次序号 (1..8)")
    p_conv.add_argument("--image", "-i", default="", help="本轮生成图片路径")
    p_conv.add_argument("--score", "-s", type=float, default=0.0, help="本轮综合评分（满分 10.0）")
    p_conv.add_argument("--dims", default="", help="五维细分得分说明")
    p_conv.add_argument("--strengths", default="", help="本轮合理/亮点之处")
    p_conv.add_argument("--defects", default="", help="本轮不合理/缺陷之处")
    p_conv.add_argument("--next-fix", default="", help="下一轮叠加修正策略")
    p_conv.add_argument(
        "--lock-text",
        default="",
        help="画师锁定微调原话，如「构图松一点」「光影锁定降到 40%%」（档位仍是 low，表上显示 95%%→75%%）",
    )
    p_conv.add_argument("--prompt", "-p", default="", help="本轮使用的 Prompt")
    p_conv.add_argument(
        "--apply",
        action="store_true",
        help="兼容旧用法：finish 默认已写入记忆，可省略；与 --no-apply 同时出现时以 --no-apply 为准",
    )
    p_conv.add_argument("--no-apply", action="store_true", help="finish 时仅结算/出报告，不写入记忆（默认会写）")
    p_conv.add_argument(
        "--verbose", "-v", action="store_true",
        help="打印完整 Markdown 报告（默认已打印评分履历表；记忆写入仍后台静默）",
    )
    p_conv.add_argument(
        "--quiet", "-q", action="store_true",
        help="仅一行结论+小提示，不打印每轮评分履历（旧静默展示）",
    )
    p_conv.add_argument("--silent", action="store_true", help="同 --quiet（兼容旧参数）")
    p_conv.add_argument("--no-silent", action="store_true", help="兼容旧参数：强制打印评分履历（现为默认）")

    p_improve = sub.add_parser("improve", help="自我迭代：扫描反思+反馈 → 更新口味档案（/pmem-improve）")
    p_improve.add_argument("action", nargs="?", default="run", choices=("run", "progress", "reflect"), help="run|progress|reflect")
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
            from skills_kit.install import command_names
            for sp in SKILL_SPECS:
                extras = " ".join(f"/{n}" for n in command_names(sp) if n != sp["name"])
                print(f"  /{sp['name']:<18} {extras}")
                print(f"     {sp['title']}")
                print(f"     ↳ {sp['description']}\n")
            return 0
        install_skills_and_agent_configs(root, quiet=False)
        return 0

    # Soft-load when memory missing (bootstrap/legacy on half-empty trees)
    mem = root / MEMORY_DIR
    if not mem.exists() and args.command in ("bootstrap", "sync", "converge"):
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
    if args.command == "ref-read":
        return cmd_ref_read(args.path)
    if args.command == "merge":
        from skills_kit.merge_relation import cmd_audit, cmd_normalize, cmd_relation_judge, cmd_split

        if args.action == "relation-judge":
            if not args.file:
                print("需要 --file merge_phase1_canonical.yaml")
                return 1
            return cmd_relation_judge(Path(args.file), args.track or None, args.all)
        if args.action == "audit":
            if not args.dir:
                print("需要 --dir 方图目录")
                return 1
            ph = Path(args.phase1) if args.phase1 else None
            return cmd_audit(Path(args.dir), ph, args.track or None)
        if args.action == "split-sheet":
            if not args.sheet or not args.dir:
                print("需要 --sheet 与 --dir")
                return 1
            return cmd_split(Path(args.sheet), Path(args.dir), args.columns)
        if args.action == "normalize":
            if not args.dir or not args.phase1 or not args.track:
                print("需要 --dir --phase1 --track")
                return 1
            return cmd_normalize(Path(args.dir), Path(args.phase1), args.track)
        if args.action == "publish":
            if not args.sheet or not args.dir or not args.phase1 or not args.track:
                print("需要 --sheet --dir --phase1 --track")
                return 1
            from skills_kit.merge_relation import audit_ladder_dir, load_phase1, parse_rows

            rc = cmd_split(Path(args.sheet), Path(args.dir), args.columns)
            if rc:
                return rc
            rows = parse_rows(load_phase1(Path(args.phase1))["tracks"][args.track])
            ok, _ = audit_ladder_dir(Path(args.dir), expected_pcts=[r.scale_pct for r in rows])
            if ok:
                print("✅ publish：audit 已通过，跳过 normalize")
                return 0
            return cmd_normalize(Path(args.dir), Path(args.phase1), args.track)
        return 1
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
        from lifecycle import cmd_doctor_lifecycle, run_doctor_quiet
        src = str(getattr(args, "source", None) or "cli")
        if getattr(args, "quiet", False):
            run_doctor_quiet(root, data, source=src, offer_tip=True)
            return 0
        rc1 = cmd_doctor_lifecycle(root, data)
        print()
        rc2 = cmd_validate(data)
        # 手动跑也刷新节流戳；用户已看全文，不再挂 tip_pending
        try:
            run_doctor_quiet(root, data, source=src, offer_tip=False)
        except Exception as exc:
            print(f"⚠️ [pmem-art] doctor state stamp failed: {exc}", file=sys.stderr)
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
    if args.command == "check-scale-gates":
        from skills_kit import check_scale_task_text, get_converge_scale_profile, find_affirmative_lock_hits
        if getattr(args, "self_check", False):
            failed = 0
            for scale in ("low", "medium", "high", "recompose"):
                dir_kw = "改为阳台花格过肩仰视" if scale == "recompose" else ""
                res = check_scale_task_text(
                    scale=scale,
                    goal=("改为阳台花格过肩仰视" if scale == "recompose" else "保媒介提升光影"),
                    recompose_dir=dir_kw,
                )
                prof = get_converge_scale_profile(scale, recompose_dir=dir_kw)
                hits = find_affirmative_lock_hits(
                    f"{prof.get('prompt_directive')}\n{prof.get('best_direction_hint')}"
                )
                ok = res["ok"] and not hits
                if scale in ("high", "recompose") and int(prof.get("min_rounds_before_stop") or 1) < 2:
                    ok = False
                status = "OK" if ok else "FAIL"
                if not ok:
                    failed += 1
                print(
                    f"[{status}] {scale}: min_rounds={prof.get('min_rounds_before_stop')} "
                    f"locks={hits or '∅'} issues={res.get('issues') or '∅'}"
                )
                print(f"         directive={prof.get('prompt_directive')}")
                print(f"         hint={prof.get('best_direction_hint')}")
            return 1 if failed else 0
        res = check_scale_task_text(
            scale=getattr(args, "scale", "high") or "high",
            goal=getattr(args, "goal", "") or "",
            prompt=getattr(args, "prompt", "") or "",
            best_direction=getattr(args, "best_direction", "") or "",
            recompose_dir=getattr(args, "recompose_dir", "") or "",
            recompose_bold=bool(getattr(args, "bold", False)),
        )
        print(
            f"{'OK' if res['ok'] else 'FAIL'} scale={res['scale']} "
            f"min_rounds={res['min_rounds_before_stop']} lock_hits={res['lock_hits'] or '∅'}"
        )
        for issue in res.get("issues") or []:
            print(f"  · {issue}")
        print(f"  directive: {res.get('prompt_directive')}")
        print(f"  hint: {res.get('best_direction_hint')}")
        return 0 if res["ok"] else 1
    if args.command == "vlm-judge":
        from vlm_judge import cmd_vlm_judge
        return cmd_vlm_judge(
            root,
            data,
            action=getattr(args, "action", "status") or "status",
            image=getattr(args, "image", "") or "",
            scale=getattr(args, "scale", "medium") or "medium",
            goal=getattr(args, "goal", "") or "",
            module=getattr(args, "module", "") or "",
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
            generate_cmd=getattr(args, "generate_cmd", "") or "",
            score=args.score,
            dims=args.dims,
            strengths=args.strengths,
            defects=args.defects,
            next_fix=args.next_fix,
            prompt=args.prompt,
            apply_memory=(not args.no_apply),
            converge_mode=getattr(args, "converge_mode", "quality") or "quality",
            scale=getattr(args, "converge_scale", "") or "",
            recompose_dir=getattr(args, "recompose_dir", "") or "",
            aspect_ratio=getattr(args, "aspect_ratio", "") or "",
            reference_image_paths=getattr(args, "reference_image_paths", "") or None,
            draft_ok=bool(getattr(args, "draft", False)),
            verbose=bool(getattr(args, "verbose", False) or getattr(args, "no_silent", False)),
            silent=(
                bool(getattr(args, "quiet", False) or getattr(args, "silent", False))
                and not bool(getattr(args, "verbose", False) or getattr(args, "no_silent", False))
            ),
            lock_text=getattr(args, "lock_text", "") or "",
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
        atlas_commands = {
            "init", "bootstrap", "sync", "accept", "place",
            "ingest", "classify-watch", "feedback", "note",
            "converge", "improve", "taste", "learn", "coach", "hook",
        }
        if any(a in atlas_commands for a in sys.argv[1:]):
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
