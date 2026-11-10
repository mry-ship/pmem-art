# -*- coding: utf-8 -*-
"""One-shot consistency audit for the icon.b SVG set. Not product code."""
import json
import math
import re
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\skill_20261110\icon_b")
NAMES = [
    "home",
    "bag",
    "map",
    "shop",
    "quest",
    "settings",
    "sprout",
    "watering-can",
]
EXPECTED_ROOT = {
    "xmlns": "http://www.w3.org/2000/svg",
    "width": "24",
    "height": "24",
    "viewBox": "0 0 24 24",
    "fill": "none",
    "stroke": "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
}


def tokenize(d: str):
    return re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", d)


def walk(d: str):
    tokens = tokenize(d)
    i = 0
    cx = cy = 0.0
    sx = sy = 0.0
    prev_cmd = ""
    prev_ctrl = None
    pts = []

    def num():
        nonlocal i
        value = float(tokens[i])
        i += 1
        return value

    def add(x, y):
        pts.append((x, y))

    while i < len(tokens):
        token = tokens[i]
        if re.fullmatch(r"[MmLlHhVvCcSsQqTtAaZz]", token):
            cmd = token
            i += 1
        else:
            cmd = prev_cmd
        absolute = cmd.isupper()
        kind = cmd.upper()
        if kind == "M":
            x, y = num(), num()
            if not absolute:
                x, y = cx + x, cy + y
            cx, cy = x, y
            sx, sy = x, y
            add(cx, cy)
            prev_cmd = "L" if absolute else "l"
            prev_ctrl = None
            continue
        if kind == "L":
            x, y = num(), num()
            if not absolute:
                x, y = cx + x, cy + y
            cx, cy = x, y
            add(cx, cy)
        elif kind == "H":
            x = num()
            cx = x if absolute else cx + x
            add(cx, cy)
        elif kind == "V":
            y = num()
            cy = y if absolute else cy + y
            add(cx, cy)
        elif kind == "C":
            vals = [num() for _ in range(6)]
            if not absolute:
                vals = [
                    cx + vals[0], cy + vals[1],
                    cx + vals[2], cy + vals[3],
                    cx + vals[4], cy + vals[5],
                ]
            add(vals[0], vals[1])
            add(vals[2], vals[3])
            add(vals[4], vals[5])
            prev_ctrl = (vals[2], vals[3])
            cx, cy = vals[4], vals[5]
        elif kind == "S":
            x2, y2, x, y = num(), num(), num(), num()
            if not absolute:
                x2, y2, x, y = cx + x2, cy + y2, cx + x, cy + y
            if prev_ctrl is not None and prev_cmd.upper() in {"C", "S"}:
                rx, ry = 2 * cx - prev_ctrl[0], 2 * cy - prev_ctrl[1]
            else:
                rx, ry = cx, cy
            add(rx, ry)
            add(x2, y2)
            add(x, y)
            prev_ctrl = (x2, y2)
            cx, cy = x, y
        elif kind == "A":
            rx, ry, rot, large, sweep, x, y = (num() for _ in range(7))
            if not absolute:
                x, y = cx + x, cy + y
            add(x, y)
            cx, cy = x, y
            prev_ctrl = None
        elif kind == "Z":
            cx, cy = sx, sy
            add(cx, cy)
            prev_ctrl = None
        else:
            raise SystemExit(f"unsupported command {cmd}")
        prev_cmd = cmd
    return pts


def main():
    rows = []
    roots = []
    for name in NAMES:
        text = (ROOT / f"{name}.svg").read_text(encoding="utf-8")
        roots.append(text.split(">", 1)[0])
        issues = []
        if "#" in text or re.search(r"\b(?:rgb|hsl)\(", text, re.I):
            issues.append("hardcoded-color")
        if "currentColor" not in text:
            issues.append("missing-currentColor")
        if re.search(r"\b(?:id|class|transform)\s*=", text):
            issues.append("id-class-or-transform")
        if text.count("<svg") != 1:
            issues.append("svg-count")
        attr = dict(re.findall(r'([\w:-]+)="([^"]*)"', text.split(">", 1)[0]))
        if attr != EXPECTED_ROOT:
            issues.append("root-attr-mismatch:" + json.dumps(attr, ensure_ascii=False))
        for raw in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text):
            if "." in raw and len(raw.split(".", 1)[1]) > 2:
                issues.append("decimals:" + raw)
        pts = []
        for d in re.findall(r'\bd="([^"]*)"', text):
            pts.extend(walk(d))
        for tag, chunk in re.findall(r"<(rect|circle)\b([^>]*)/?>", text):
            vals = {k: float(v) for k, v in re.findall(r'([\w:-]+)="([^"]*)"', chunk) if re.fullmatch(r"[-+]?(?:\d*\.\d+|\d+)", v)}
            if tag == "rect":
                x, y, w, h = vals["x"], vals["y"], vals["width"], vals["height"]
                pts.extend([(x, y), (x + w, y + h)])
            else:
                pts.extend([(vals["cx"] - vals["r"], vals["cy"] - vals["r"]), (vals["cx"] + vals["r"], vals["cy"] + vals["r"])])
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        pad = 1.0
        box = {
            "min_x": round(min(xs) - pad, 2),
            "min_y": round(min(ys) - pad, 2),
            "max_x": round(max(xs) + pad, 2),
            "max_y": round(max(ys) + pad, 2),
        }
        if box["min_x"] < 1.5 or box["min_y"] < 1.5 or box["max_x"] > 22.5 or box["max_y"] > 22.5:
            issues.append("padding")
        width = box["max_x"] - box["min_x"]
        height = box["max_y"] - box["min_y"]
        rows.append({
            "file": name + ".svg",
            "issues": issues,
            "ink_box": box,
            "ink_w": round(width, 2),
            "ink_h": round(height, 2),
            "paths": len(re.findall(r"<path\b", text)),
            "shapes": len(re.findall(r"<(?:path|rect|circle)\b", text)),
        })
    same_root = len(set(roots)) == 1
    report = {"same_root": same_root, "icons": rows}
    out = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\skill_20261110\reports\_audit_icon_b.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
