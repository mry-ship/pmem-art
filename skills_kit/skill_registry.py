"""Build the skill route index from SKILL_SPECS. Disk skills that were not installed are ignored."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_DRAW_HEADING = {
    "界面": ("ui.kit", "pmem-ui"),
    "图标": None,  # A/B/C come from the icon skill, not this one row
    "合成梯": ("merge.ladder", "pmem-merge-ladder"),
    "镜头包": ("draw.lens", "pmem-draw"),
    "克隆": ("draw.clone", "pmem-draw"),
    "变体": ("draw.variant", "pmem-draw"),
    "多图分工": ("draw.multi", "pmem-draw"),
    "原画": ("draw.key", "pmem-draw"),
    "普通图": ("draw.ordinary", "pmem-draw"),
}

_ONE_SECTION = {
    "pmem-style-lock": ("style.lock", "以后按这张画"),
    "pmem-critique": ("critique.review", "只审、不画"),
    "pmem-atlas": ("atlas.file", "散图归位"),
    "pmem-coach": ("coach.report", "要看进步、短板、知识卡"),
    "pmem-prompt": ("prompt.write", "要写提示词、扩写 brief"),
    "pmem-merge-ladder": ("merge.ladder", "同一套东西一档比一档更大"),
    "pmem-ui": ("ui.kit", "整屏、HUD、弹窗套件、九宫格、按钮状态"),
}


def _headings(body: str) -> list[str]:
    return [line.strip() for line in body.splitlines() if line.startswith("## ")]


def _first_heading(body: str) -> str:
    found = _headings(body)
    if found:
        return found[0]
    return _skill_open(body)


def _skill_open(body: str) -> str:
    """The skill's own first line. One-section skills open here, not at a later ##."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped
    return ""


def _frontmatter_name(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    block = text[3:end]
    m = re.search(r"^name:\s*(\S+)\s*$", block, flags=re.M)
    return m.group(1) if m else ""


def _parse_draw_table(body: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    in_table = False
    for line in body.splitlines():
        if line.startswith("| 认成"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if re.match(r"^\|\s*:?-{2,}", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        name = re.sub(r"\*+", "", cells[0]).strip()
        when = re.sub(r"\*+", "", cells[1]).strip()
        nxt = cells[2].strip()
        rows.append((name, when, nxt))
    return rows


def _parse_tighten(body: str) -> list[str]:
    lines = body.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if "认不准时" in line:
            start = i + 1
            break
    out: list[str] = []
    for line in lines[start:]:
        m = re.match(r"^\d+\.\s+(.*)$", line.strip())
        if m:
            out.append(re.sub(r"\*+", "", m.group(1)).strip())
            continue
        if out and line.startswith("#"):
            break
        if out and line.strip() == "---":
            break
    return out


def _mode_heading(body: str, letter: str) -> str:
    """Dedicated Mode A/B/C section, not the shared Step 5 converge heading."""
    hits: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        if f"Mode {letter}" not in stripped:
            continue
        if "Step" in stripped or "关键枚" in stripped:
            continue
        hits.append(stripped)
    return hits[0] if hits else ""


def _icon_routes(body: str) -> list[dict[str, Any]]:
    """Mode A/B/C from the分流 section, pointed at the heading that section names."""
    spec = (
        ("icon.a", "A", "桌面图标、1024 母版"),
        ("icon.b", "B", "一套线性 SVG"),
        ("icon.c", "C", "背包道具格"),
    )
    routes: list[dict[str, Any]] = []
    for rid, letter, when in spec:
        heading = _mode_heading(body, letter)
        routes.append(
            {
                "id": rid,
                "when": when,
                "skill": "pmem-icon",
                "section": f"Mode {letter}",
                "file": ".cursor/skills/pmem-icon/SKILL.md",
                "heading": heading,
                "routable": bool(heading),
                "simultaneous_pixels": False,
            }
        )
    return routes


def _contract_heading(body: str, section: str) -> str:
    if section == "普通图":
        for line in _headings(body):
            if line.startswith("## 二、"):
                return line
        return ""
    needle = f"## 合同 · {section}"
    for line in _headings(body):
        if line.startswith(needle):
            return line
    return ""


def build_registry(specs: list[dict[str, Any]], *, installed_root: Path | None = None) -> dict[str, Any]:
    by_name = {spec["name"]: spec for spec in specs}
    draw_body = by_name["pmem-draw"]["body"]
    tighten = _parse_tighten(draw_body)
    routes: list[dict[str, Any]] = []
    seen: set[str] = set()

    for name, when, _nxt in _parse_draw_table(draw_body):
        mapped = _DRAW_HEADING.get(name)
        if mapped is None:
            continue
        rid, skill = mapped
        if rid in seen:
            continue
        body = by_name[skill]["body"]
        if skill == "pmem-draw":
            heading = _contract_heading(draw_body, name)
            section = name
        else:
            heading = _skill_open(body)
            section = by_name[skill]["title"]
        routes.append(
            {
                "id": rid,
                "when": when,
                "skill": skill,
                "section": section,
                "file": f".cursor/skills/{skill}/SKILL.md",
                "heading": heading,
                "routable": bool(heading),
                "simultaneous_pixels": False,
            }
        )
        seen.add(rid)

    for route in _icon_routes(by_name["pmem-icon"]["body"]):
        if route["id"] not in seen:
            routes.append(route)
            seen.add(route["id"])

    for skill, (rid, when) in _ONE_SECTION.items():
        if rid in seen or skill not in by_name:
            continue
        heading = _skill_open(by_name[skill]["body"])
        routes.append(
            {
                "id": rid,
                "when": when,
                "skill": skill,
                "section": by_name[skill]["title"],
                "file": f".cursor/skills/{skill}/SKILL.md",
                "heading": heading,
                "routable": bool(heading),
                "simultaneous_pixels": False,
            }
        )
        seen.add(rid)

    # 普通图是兜底，必须排在最后。图标和锁风格若排在它前面，按「第一条命中」才不会被「以上都不是」截走。
    phase = {
        "ui.kit": 10,
        "icon.a": 20,
        "icon.b": 21,
        "icon.c": 22,
        "merge.ladder": 30,
        "draw.lens": 40,
        "draw.clone": 50,
        "draw.variant": 60,
        "draw.multi": 70,
        "draw.key": 80,
        "style.lock": 90,
        "critique.review": 91,
        "atlas.file": 92,
        "coach.report": 93,
        "prompt.write": 94,
        "draw.ordinary": 100,
    }
    for route in routes:
        route["phase"] = phase.get(route["id"], 99)
    routes.sort(key=lambda r: (r["phase"], r["id"]))

    draw_contracts = [
        line for line in _headings(draw_body) if line.startswith("## 合同 · ")
    ]
    routed_headings = {r["heading"] for r in routes if r["skill"] == "pmem-draw"}
    unroutable = [line for line in draw_contracts if line not in routed_headings]

    frontmatter_ok = True
    stale: list[str] = []
    if installed_root is not None:
        for spec in specs:
            path = installed_root / ".cursor" / "skills" / spec["name"] / "SKILL.md"
            if not path.exists():
                frontmatter_ok = False
                stale.append(spec["name"])
                continue
            got = _frontmatter_name(path.read_text(encoding="utf-8"))
            if got != spec["name"]:
                frontmatter_ok = False
                stale.append(spec["name"])

    return {
        "source": "skills_kit/skill_specs.py",
        "frontmatter_ok": frontmatter_ok,
        "stale_skills": stale,
        "tighten": tighten,
        "routes": routes,
        "unroutable_headings": unroutable,
    }


def render_registry_md(reg: dict[str, Any]) -> str:
    lines = [
        "# 技能注册表",
        "",
        f"来源：`{reg['source']}`。生成：`python3 pmem_art.py skills --install`。",
        "",
    ]
    if not reg.get("frontmatter_ok", True):
        stale = "、".join(reg.get("stale_skills") or [])
        lines.append(f"frontmatter_ok: false。这些技能要重新安装：{stale}。")
        lines.append("")
    lines.append("## tighten")
    lines.append("")
    for i, item in enumerate(reg.get("tighten") or [], start=1):
        lines.append(f"{i}. {item}")
    lines.append("")
    lines.append("## 路由")
    lines.append("")
    lines.append("按 phase 从小到大对，停在第一条对上的行。普通图 phase 最大，只作兜底，不要把它的「以上都不是」当成关键词命中。")
    lines.append("")
    lines.append("| id | phase | when | skill | heading | routable |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for route in reg.get("routes") or []:
        heading = str(route["heading"]).replace("|", "\\|")
        lines.append(
            f"| `{route['id']}` | {route.get('phase', '')} | {route['when']} | `{route['skill']}` | {heading} | {str(route['routable']).lower()} |"
        )
    lines.append("")
    lines.append("## unroutable_headings")
    lines.append("")
    extra = reg.get("unroutable_headings") or []
    if not extra:
        lines.append("（无）")
    else:
        for item in extra:
            lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def write_registry_files(root: Path, specs: list[dict[str, Any]]) -> dict[str, Any]:
    reg = build_registry(specs, installed_root=root)
    payload = json.dumps(reg, ensure_ascii=False, indent=2) + "\n"
    markdown = render_registry_md(reg)
    for base in (root / ".cursor" / "skills", root / ".claude" / "skills", root / ".agents" / "skills"):
        base.mkdir(parents=True, exist_ok=True)
        (base / "registry.json").write_text(payload, encoding="utf-8")
        (base / "registry.md").write_text(markdown, encoding="utf-8")
    return reg
