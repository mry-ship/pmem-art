"""Build the skill route index from SKILL_SPECS. Disk skills that were not installed are ignored."""
from __future__ import annotations

from .platform_cli import pmem_art_cli
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
    "pmem-merge-ladder": ("merge.ladder", "同域升级梯默认整表一组八档；点名数量或参考跟格数"),
    "pmem-ui": ("ui.kit", "整屏、HUD、弹窗套件、九宫格、按钮状态"),
}


def _headings(body: str) -> list[str]:
    return [line.strip() for line in body.splitlines() if line.startswith("## ")]


def slice_markdown_section(body: str, heading: str) -> str:
    """按 heading 裁到下一同级/更高级标题；忽略围栏代码块内以 # 开头的行（防 bash 注释截断）。"""
    want = (heading or "").strip()
    if not want:
        return ""
    lines = body.splitlines()
    start = -1
    for i, ln in enumerate(lines):
        if ln.strip() == want:
            start = i
            break
    if start < 0:
        return ""
    level = len(want) - len(want.lstrip("#"))
    if level <= 0:
        level = 1
    end = len(lines)
    in_fence = False
    for j in range(start + 1, len(lines)):
        raw = lines[j]
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("#"):
            lv = len(stripped) - len(stripped.lstrip("#"))
            if lv <= level:
                end = j
                break
    return "\n".join(lines[start:end])


def slice_route_body(body: str, route: dict[str, Any]) -> str:
    """按 route.pack_headings（缺省则 [heading]）顺序拼接多节，供总控交给执行侧。"""
    headings = list(route.get("pack_headings") or [])
    primary = str(route.get("heading") or "").strip()
    if not headings and primary:
        headings = [primary]
    parts: list[str] = []
    seen: set[str] = set()
    for h in headings:
        want = (h or "").strip()
        if not want or want in seen:
            continue
        seen.add(want)
        chunk = slice_markdown_section(body, want).strip()
        if chunk:
            parts.append(chunk)
    return "\n\n".join(parts)


def _h2_by_prefix(body: str, prefix: str) -> str:
    for line in _headings(body):
        if line.startswith(prefix):
            return line
    return ""


def _any_heading(body: str, exact: str) -> str:
    want = (exact or "").strip()
    if not want:
        return ""
    for line in body.splitlines():
        if line.strip() == want:
            return want
    return ""


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
    """Mode A/B/C + 该 Mode 交付清单 + 记忆静默，打包进 pack_headings。"""
    spec = (
        ("icon.a", "A", "桌面图标、1024 母版"),
        ("icon.b", "B", "一套线性 SVG"),
        ("icon.c", "C", "背包道具格"),
    )
    memory = _h2_by_prefix(body, "## 记忆静默")
    routes: list[dict[str, Any]] = []
    for rid, letter, when in spec:
        heading = _mode_heading(body, letter)
        checklist = _any_heading(body, f"### Mode {letter}")
        pack = [h for h in (heading, checklist, memory) if h]
        routes.append(
            {
                "id": rid,
                "when": when,
                "skill": "pmem-icon",
                "section": f"Mode {letter}",
                "file": ".cursor/skills/pmem-icon/SKILL.md",
                "heading": heading,
                "pack_headings": pack,
                "routable": bool(heading),
                "simultaneous_pixels": False,
            }
        )
    return routes


def _contract_heading(body: str, section: str) -> str:
    if section == "普通图":
        return _h2_by_prefix(body, "## 二、")
    needle = f"## 合同 · {section}"
    for line in _headings(body):
        if line.startswith(needle):
            return line
    return ""


def _draw_pack_headings(body: str, section: str, heading: str) -> list[str]:
    """出图合同：零点五 route + 执行卡（优先）/第二节 + 合同 + 记忆静默。"""
    route_gate = _h2_by_prefix(body, "## 零点五")
    card = _h2_by_prefix(body, "## 执行卡")
    loop = _h2_by_prefix(body, "## 二、")
    # 有执行卡则不再塞整节「二、」（降合规长度）；卡内须含 reasonableness/converge 关键词
    loop_or_card = card or loop
    memory = _h2_by_prefix(body, "## 记忆静默")
    if section == "普通图":
        return [h for h in (route_gate, loop_or_card or heading, memory) if h]
    if section == "镜头包":
        return [h for h in (route_gate, heading) if h]
    # 克隆 / 变体 / 多图分工 / 原画：公共闭环 + 叠加合同
    return [h for h in (route_gate, loop_or_card, heading, memory) if h]


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
            pack = _draw_pack_headings(draw_body, name, heading)
        else:
            heading = _skill_open(body)
            section = by_name[skill]["title"]
            if rid == "merge.ladder":
                card = _h2_by_prefix(body, "## 执行卡")
                forbid = _h2_by_prefix(body, "## 禁止")
                pack = [h for h in (card, forbid) if h] or ([heading] if heading else [])
            elif rid in {"ui.kit", "prompt.write"}:
                card = _h2_by_prefix(body, "## 执行卡")
                pack = [card] if card else ([heading] if heading else [])
            else:
                pack = [heading] if heading else []
        routes.append(
            {
                "id": rid,
                "when": when,
                "skill": skill,
                "section": section,
                "file": f".cursor/skills/{skill}/SKILL.md",
                "heading": heading,
                "pack_headings": pack,
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
        body = by_name[skill]["body"]
        heading = _skill_open(body)
        card = _h2_by_prefix(body, "## 执行卡")
        if rid == "prompt.write" and card:
            pack = [card]
        elif rid == "merge.ladder":
            forbid = _h2_by_prefix(body, "## 禁止")
            pack = [h for h in (card, forbid) if h] or ([heading] if heading else [])
        elif rid == "ui.kit" and card:
            pack = [card]
        else:
            pack = [heading] if heading else []
        routes.append(
            {
                "id": rid,
                "when": when,
                "skill": skill,
                "section": by_name[skill]["title"],
                "file": f".cursor/skills/{skill}/SKILL.md",
                "heading": heading,
                "pack_headings": pack,
                "routable": bool(heading),
                "simultaneous_pixels": False,
            }
        )
        seen.add(rid)

    # phase 只决定注册表阅读顺序。分流以 plan_route / route_ids 为准，不按第一条 phase 改判。
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

    # heading 字符串命中 ≠ 按节裁剪正确：校验 Icon Mode 节互不吞并；出图 pack 含闭环
    section_cut_ok = True
    section_cut_fails: list[str] = []
    by_rid = {r["id"]: r for r in routes}
    icon_body = by_name.get("pmem-icon", {}).get("body") or ""
    if icon_body:
        checks = (
            ("icon.a", ("Mode A",), ("## 三、Mode B", "## 四、Mode C")),
            ("icon.b", ("Mode B", "### B6"), ("## 四、Mode C",)),
            ("icon.c", ("Mode C",), ("## 三、Mode B", "### B6")),
        )
        for rid, must_have, must_not in checks:
            route = by_rid.get(rid) or {}
            heading = str(route.get("heading") or "")
            if not heading.startswith("## "):
                section_cut_ok = False
                section_cut_fails.append(f"{rid}:heading_not_h2")
                continue
            mode_only = slice_markdown_section(icon_body, heading)
            for needle in must_have:
                if needle not in mode_only:
                    section_cut_ok = False
                    section_cut_fails.append(f"{rid}:missing:{needle}")
            for bad in must_not:
                if bad in mode_only:
                    section_cut_ok = False
                    section_cut_fails.append(f"{rid}:leaked:{bad}")
            packed = slice_route_body(icon_body, route)
            for needle in (f"### Mode {rid[-1].upper()}", "记忆静默"):
                if needle not in packed:
                    section_cut_ok = False
                    section_cut_fails.append(f"{rid}:pack_missing:{needle}")
            # Mode A must not leak SVG B rules; must keep Light-only / 点名三态.
            if rid == "icon.a":
                if "currentColor" in packed:
                    section_cut_ok = False
                    section_cut_fails.append("icon.a:leaked:currentColor")
                if "仅玩家点名" not in packed and "仅点名" not in packed:
                    section_cut_ok = False
                    section_cut_fails.append("icon.a:pack_missing:仅点名三态")
            if rid == "icon.b" and "满幅直角" in packed and "Mode A" in packed:
                section_cut_ok = False
                section_cut_fails.append("icon.b:leaked:ModeA满幅")

    for rid, must in (
        ("draw.clone", ("reasonableness", "converge judge", "合同 · 克隆", "零点五")),
        ("draw.variant", ("reasonableness", "converge judge", "合同 · 变体")),
        ("draw.multi", ("reasonableness", "converge judge", "合同 · 多图分工")),
        ("draw.key", ("reasonableness", "converge judge", "合同 · 原画")),
        ("draw.ordinary", ("reasonableness", "converge judge", "零点五", "执行卡")),
    ):
        route = by_rid.get(rid) or {}
        packed = slice_route_body(draw_body, route)
        for needle in must:
            if needle not in packed:
                section_cut_ok = False
                section_cut_fails.append(f"{rid}:pack_missing:{needle}")

    return {
        "source": "skills_kit/skill_specs.py",
        "frontmatter_ok": frontmatter_ok,
        "stale_skills": stale,
        "tighten": tighten,
        "routes": routes,
        "unroutable_headings": unroutable,
        "section_cut_ok": section_cut_ok,
        "section_cut_fails": section_cut_fails,
    }


def render_registry_md(reg: dict[str, Any]) -> str:
    lines = [
        "# 技能注册表",
        "",
        f"来源：`{reg['source']}`。生成：`{pmem_art_cli()} skills --install`。",
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
    lines.append(
        f"执行以 `{pmem_art_cli()} route` 的 `route_ids` 为准。"
        "这张表核对 heading；**交给执行侧用 `pack_headings` + `slice_route_body`**"
        "（出图合同=零点五+第二节+合同；图标=Mode+§五清单+记忆静默）。"
        "phase 是查阅顺序，不要用它改判。普通图 phase 最大，只作兜底。"
    )
    lines.append("")
    lines.append("| id | phase | when | skill | heading | pack | routable |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for route in reg.get("routes") or []:
        heading = str(route["heading"]).replace("|", "\\|")
        pack = " + ".join(
            (h[:22] + "…" if len(h) > 22 else h).replace("|", "\\|")
            for h in (route.get("pack_headings") or [route["heading"]])
        )
        lines.append(
            f"| `{route['id']}` | {route.get('phase', '')} | {route['when']} | `{route['skill']}` | {heading} | {pack} | {str(route['routable']).lower()} |"
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
    lines.append("## section_cut")
    lines.append("")
    if reg.get("section_cut_ok", True):
        lines.append(
            "ok：Icon Mode 互不吞并且 pack 含清单；"
            "draw.clone/variant/multi/key/ordinary 的 `slice_route_body` 含 reasonableness/闭环。"
        )
    else:
        fails = "、".join(reg.get("section_cut_fails") or []) or "unknown"
        lines.append(f"fail：{fails}。须修 pack_headings / skill_specs 层级或围栏内伪 H1。")
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
