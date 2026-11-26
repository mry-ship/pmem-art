"""Tolerant YAML loader (PyYAML when present, built-in fallback otherwise)."""
from __future__ import annotations

import json
import re
from typing import Any


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
