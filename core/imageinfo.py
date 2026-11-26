"""PNG / JPEG / WebP header probing. No third-party deps."""
from __future__ import annotations

import base64
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


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


def inspect_png(path: Path, *, embed_data_uri: bool = True) -> dict[str, Any]:
    """Read PNG / JPEG / WebP headers for size, mode, and alpha. PNG also keeps tEXt.

    embed_data_uri=False skips base64 (atlas / index path — keeps HTML small).
    """
    if not path.is_file():
        return {"exists": False, "path": str(path)}
    raw = path.read_bytes()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    size_kb = round(len(raw) / 1024, 1)
    mime = _image_mime(path)
    b64_uri = ""
    if embed_data_uri:
        b64_uri = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")

    def _pack(**extra: Any) -> dict[str, Any]:
        out = {
            "exists": True,
            "size_kb": size_kb,
            "sha256_16": sha16,
            **extra,
        }
        if embed_data_uri:
            out["data_uri"] = b64_uri
        return out

    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        jpeg = _jpeg_size(raw)
        webp = None if jpeg else _webp_size(raw)
        if jpeg:
            width, height = jpeg
            return _pack(
                width=width,
                height=height,
                resolution=f"{width}x{height}",
                bit_depth=8,
                mode="RGB",
                has_alpha=False,
                png_meta={},
            )
        if webp:
            width, height, has_alpha = webp
            return _pack(
                width=width,
                height=height,
                resolution=f"{width}x{height}",
                bit_depth=8,
                mode="RGBA" if has_alpha else "RGB",
                has_alpha=has_alpha,
                png_meta={},
            )
        return _pack()

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
    return _pack(
        width=width,
        height=height,
        resolution=f"{width}x{height}",
        bit_depth=bit_depth,
        mode=mode,
        has_alpha=has_alpha,
        png_meta=text_meta,
    )
