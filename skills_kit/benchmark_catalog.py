"""商业对标范例卡：只出气质句与档序，禁止把竞品图当垫图像素。

卡库存放：
- 打包：skills_kit/data/benchmarks/*.yaml
- 项目覆盖：.memory-art/benchmarks/*.yaml
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_PACK_DIR = Path(__file__).resolve().parent / "data" / "benchmarks"
_PROJECT_REL = Path(".memory-art") / "benchmarks"

# 垫图路径若落在这些目录 → 拒
_FORBIDDEN_PAD_MARKERS = (
    "/benchmarks/",
    "\\.memory-art\\benchmarks\\",
    "skills_kit/data/benchmarks",
    "docs/COMMERCIAL_BENCHMARK",
)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """极简 YAML（只够本卡用）：key: value / key:\\n  - item。"""
    out: dict[str, Any] = {}
    list_key: str | None = None
    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if list_key and line.startswith("  - "):
            bucket = out.setdefault(list_key, [])
            if isinstance(bucket, list):
                bucket.append(line[4:].strip().strip("'\""))
            continue
        list_key = None
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        if not val:
            list_key = key
            out[key] = []
            continue
        if val.lower() in ("true", "false"):
            out[key] = val.lower() == "true"
        else:
            out[key] = val
    return out


def _load_file(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get("id"):
        # id 默认用文件名
        data = dict(data or {})
        data.setdefault("id", path.stem)
    data["id"] = str(data["id"]).strip()
    data["_path"] = str(path)
    data.setdefault("forbid_pad", True)
    return data


def list_benchmark_dirs(root: Path | None = None) -> list[Path]:
    dirs: list[Path] = []
    if _PACK_DIR.is_dir():
        dirs.append(_PACK_DIR)
    if root is not None:
        proj = Path(root) / _PROJECT_REL
        if proj.is_dir():
            dirs.append(proj)
    return dirs


def load_all_cards(root: Path | None = None) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for d in list_benchmark_dirs(root):
        for path in sorted(d.glob("*.yaml")) + sorted(d.glob("*.yml")):
            card = _load_file(path)
            if card and card.get("id"):
                cards[str(card["id"])] = card
    return cards


def lookup(
    query: str,
    *,
    root: Path | None = None,
    category: str = "",
) -> dict[str, Any]:
    """按 id / category / 关键词查一张卡。"""
    cards = load_all_cards(root)
    q = (query or category or "").strip().lower()
    if not q and category:
        q = category.strip().lower()
    if not cards:
        return {
            "ok": False,
            "error": "no_benchmark_cards",
            "hint": "缺少 skills_kit/data/benchmarks；请升级 pmem-art 或自建 .memory-art/benchmarks/",
        }
    if q in cards:
        return {"ok": True, "card": cards[q], "match": "id"}
    # category 精确
    for card in cards.values():
        if str(card.get("category") or "").strip().lower() == q:
            return {"ok": True, "card": card, "match": "category"}
    # 关键词
    hits: list[dict[str, Any]] = []
    for card in cards.values():
        blob = " ".join(
            str(card.get(k) or "")
            for k in ("id", "category", "aliases", "surface", "layout_notes", "title")
        ).lower()
        aliases = card.get("aliases")
        if isinstance(aliases, list):
            blob += " " + " ".join(str(a).lower() for a in aliases)
        if q and q in blob:
            hits.append(card)
    if len(hits) == 1:
        return {"ok": True, "card": hits[0], "match": "keyword"}
    if len(hits) > 1:
        return {
            "ok": False,
            "error": "ambiguous",
            "candidates": [h.get("id") for h in hits[:8]],
            "hint": "请用更具体的 --category / id",
        }
    # 回落 COMMERCIAL_BENCHMARK 气质表提示
    return {
        "ok": False,
        "error": "not_found",
        "hint": "查 docs/COMMERCIAL_BENCHMARK.md 填一句泛气质；禁止编造具体竞品档名。认不出品类就问人。",
        "ids": sorted(cards.keys()),
    }


def format_card(card: dict[str, Any]) -> str:
    lines = [
        f"benchmark_id: {card.get('id')}",
        f"category: {card.get('category') or ''}",
        f"surface: {card.get('surface') or ''}",
    ]
    if card.get("layout_notes"):
        lines.append(f"layout_notes: {card.get('layout_notes')}")
    levels = card.get("ladder_levels") or []
    if isinstance(levels, list) and levels:
        lines.append("ladder_levels:")
        for lv in levels:
            lines.append(f"  - {lv}")
    lines.append(f"forbid_pad: {bool(card.get('forbid_pad', True))}")
    lines.append("规则: 只抽气质/档序写入 brief；禁止把本卡或竞品截图路径写入 --reference-image-paths。")
    return "\n".join(lines)


def path_is_forbidden_benchmark_pad(path: str) -> bool:
    p = (path or "").replace("\\", "/")
    low = p.lower()
    for m in _FORBIDDEN_PAD_MARKERS:
        if m.replace("\\", "/").lower() in low:
            return True
    if re.search(r"(^|/)\.memory-art/benchmarks(/|$)", low):
        return True
    return False


def assert_refs_not_benchmark_pads(paths: list[str] | tuple[str, ...] | None) -> tuple[bool, str]:
    bad = [p for p in (paths or []) if path_is_forbidden_benchmark_pad(str(p))]
    if not bad:
        return True, ""
    shown = "、".join(str(p) for p in bad[:4])
    return False, f"禁止把商业对标范例目录当垫图：{shown}"


def cmd_benchmark(
    root: Path,
    *,
    action: str = "lookup",
    query: str = "",
    category: str = "",
) -> int:
    act = (action or "lookup").strip().lower()
    if act in ("list", "ls"):
        cards = load_all_cards(root)
        if not cards:
            print("（无范例卡）")
            return 1
        for cid, card in sorted(cards.items()):
            print(f"{cid}\t{card.get('category') or ''}\t{(card.get('surface') or '')[:60]}")
        return 0
    result = lookup(query or category, root=root, category=category)
    if not result.get("ok"):
        print(f"❌ benchmark: {result.get('error')} — {result.get('hint')}")
        if result.get("candidates"):
            print("candidates:", ", ".join(str(c) for c in result["candidates"]))
        elif result.get("ids"):
            print("known ids:", ", ".join(str(i) for i in result["ids"][:20]))
        return 1
    card = result["card"]
    print(format_card(card))
    return 0
