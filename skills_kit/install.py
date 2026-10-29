"""Install skills and agent config stubs."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .skill_specs import SKILL_SPECS

def _render_skill_md(spec: dict[str, Any], command_name: str) -> str:
    return (
        f"---\n"
        f"name: {command_name}\n"
        f"description: {spec['description']}\n"
        f"---\n\n"
        f"{spec['body'].strip()}\n"
    )


def command_names(spec: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for nm in [spec["name"], spec.get("alias"), *list(spec.get("aliases") or [])]:
        if nm and nm not in names:
            names.append(nm)
    return names


def _route_banner(spec: dict[str, Any], command_name: str) -> str:
    route = (spec.get("alias_routes") or {}).get(command_name)
    if not route:
        return ""
    return (
        f"> **点名锁定**：玩家用了 `/{command_name}`，类型固定为 **{route}**。"
        "不要改判，不要改问。下面只执行这一支。\n\n"
    )


def _render_command_md(spec: dict[str, Any], command_name: str) -> str:
    return (
        f"---\n"
        f"description: {spec['title']}（pmem-art）\n"
        f"---\n\n"
        f"{_route_banner(spec, command_name)}"
        f"{spec['body'].strip()}\n"
    )


AGENT_DOC_MARKER_START = "<!-- pmem-art:skills:start -->"
AGENT_DOC_MARKER_END = "<!-- pmem-art:skills:end -->"


def _render_agent_doc_block() -> str:
    return f"""{AGENT_DOC_MARKER_START}
## 🎨 pmem-art 美术记忆系统与内置斜杠技能（Skills）

本项目挂载了 **pmem-art**（面向 Cursor / Claude Code / Codex 的个人美术积累记忆与闭环自评生图系统）。

### 1. 总控优先，点名仍按点名走
- 玩家没点名具体技能时，走 `/pmem-agent`。总控只审一轮：查合理性、缺漏和理解错误，先把分析列出来。只有一种确定情况就直接执行；多种情况列出来等玩家确认，确认前不执行。玩家另提要求就再审一遍，仍要等确认后再执行。总控自己不生图。路径/版式/「再跑一遍」同范围等可默认项直接写入分析；只有交付物类型或身份题材会做错才算多种情况。
- 玩家点名了界面、图标、合成梯、原画、克隆、变体或镜头包，就按点名走，不再绕总控。
- 总控选定后回显 `banner`（【按 XX 走了】或【走默认路径】），只说明选了哪一支，不问选哪条技能。没点名时先把口语收成一行标准路由句，再跑 `python3 pmem_art.py route --text "…" --canonical "…"`（字面 n-gram+口语扩展，非语义向量；禁止整库进上下文）。流程图见 `docs/route_pipeline.html`。
- 平时一次只走一支。定稿若是整页展陈/对比页/多技能同范围重跑，允许按清单依次点名多支，最后收新 HTML。判成界面、图标或合成梯时，先读对应技能再动手，禁止用普通单张合同交差。
- 有参考但没说新题材 → 普通图，不进克隆。没人要几套机位 → 不进镜头包，点选前不生图。
- 交出去的是定稿和每一张图，不能在调用前收成一张参考图。
- 锁风格、只审图、归档、教练、提示词生成不进自动生图。
- 生图闭环最多 **4 轮**，合格线仍是 ≥9.5。不到线就改，满 4 轮挑最高分。合成梯的八件档位不变。关系讨论固定 3 稿，把升级链和画风定清楚。合成说不通就不能出图；那一段不是跑图。

### 2. 内置快捷技能（在对话框直接输入 `/技能名` 即可触发）

| 技能指令 | 用途说明 |
| :--- | :--- |
| **`/pmem-agent`** | **总控**。没点名具体技能时走这一条。一轮审核：确定就列出分析并直接执行；多种情况先列出来等确认。另提要求则再审一遍，确认后再执行。可默认则默认。对比展陈可依次点名多支。结算格式仍是被调用那一支自己的 |
| **`/pmem-draw`** | **生图**。普通图 / 原画 / 克隆 / 变体 / 镜头包在这一条里。点名了类型就按点名做 |
| **`/pmem-ui`** | **整套界面**。概念先行→组件表→九宫格→状态族。判成界面才走，禁止用单张插画代替 |
| **`/pmem-icon`** | **图标**。A 桌面母版 / B 线性 SVG / C 道具格，三档不混 |
| **`/pmem-merge-ladder`** | **合成梯**。先用 3 稿把升级链和画风定清楚，再一档一张正方形。同框只是体量预览，不是成品 |
| **`/pmem-prompt`** | **提示词**。把玩家原话按合理性/美观/画风/特写等扩成 2～4 套可选方案（或唯一方案）。不生图 |
| **`/pmem-style-lock`** | **锁风格**。从样张抽色板、光影、禁用词。不进自动生图 |
| **`/pmem-critique`** | **只审图**。六维挑刺，翻车点记入红线。不生图 |
| **`/pmem-atlas`** | **归档**。散图归位并刷新 `art-atlas.html` |
| **`/pmem-coach`** | **进阶偷看**。进步 / 短板 / 知识合成一条。知识卡要玩家说收下才写入 |

### 3. 评分履历可见 · 记忆静默写入（默认）
- 闭环每轮须向用户展示：六维分、不足、下一轮改点；`converge finish` 默认打印全轮评分履历并写记忆（`--no-apply` 可跳过；只要终稿加 `--quiet`）。
- `finish` / 高信号 `feedback` 后仍自动写反思、更新 taste、强化 recipe/红线、悄悄排队 learn——**不要**旁白记忆写入；最多转述一行「小提示」。
- 进步、短板、知识卡用 `/pmem-coach`。知识卡没有玩家明确收下，不要写入。

### 4. 日常自然语言反馈沉淀（无需手写 YAML）
- 生图前先运行：`python3 pmem_art.py search --module <模块>` 或 `python3 pmem_art.py search "<关键词>"`
- 当画师说「太赛博 / 头太大 / 别这样画 / 这版留着 / 换成水彩 / 以后都用…」时，立即运行：
  `python3 pmem_art.py feedback "<画师原话>" --module <模块> [--asset <图片路径>]`
- 运行闭环收敛追踪器：`python3 pmem_art.py converge start`，然后每轮 `converge generate` 与 `converge judge`，最后 `converge finish`（默认打印评分履历）
{AGENT_DOC_MARKER_END}
"""


def _upsert_markdown_block(file_path: Path, header_title: str) -> None:
    block = _render_agent_doc_block()
    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        if AGENT_DOC_MARKER_START in content and AGENT_DOC_MARKER_END in content:
            pre = content.split(AGENT_DOC_MARKER_START)[0]
            post = content.split(AGENT_DOC_MARKER_END)[1]
            file_path.write_text(pre.rstrip() + "\n\n" + block + "\n" + post.lstrip(), encoding="utf-8")
        else:
            file_path.write_text(content.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
    else:
        file_path.write_text(f"# {header_title}\n\n{block}\n", encoding="utf-8")


def install_skills_and_agent_configs(root: Path, quiet: bool = False) -> dict[str, list[str]]:
    """
    在目标项目根目录自动安装：
    - Cursor Skills & Slash Commands: .cursor/skills/<name>/SKILL.md, .cursor/commands/<name>.md
    - Claude Code Skills & Commands : .claude/skills/<name>/SKILL.md, .claude/commands/<name>.md, CLAUDE.md
    - Codex / Agents Skills         : .agents/skills/<name>/SKILL.md, AGENTS.md
    """
    installed: dict[str, list[str]] = {
        "cursor_skills": [],
        "cursor_commands": [],
        "claude_skills": [],
        "claude_commands": [],
        "codex_skills": [],
        "agent_docs": [],
    }

    for spec in SKILL_SPECS:
        # One skill folder and one /pmem- command per contract.
        for base in (root / ".cursor" / "skills", root / ".claude" / "skills", root / ".agents" / "skills"):
            skill_path = base / spec["name"] / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(_render_skill_md(spec, spec["name"]), encoding="utf-8")
        installed["cursor_skills"].append(str((root / ".cursor" / "skills" / spec["name"] / "SKILL.md").relative_to(root)))
        installed["claude_skills"].append(str((root / ".claude" / "skills" / spec["name"] / "SKILL.md").relative_to(root)))
        installed["codex_skills"].append(str((root / ".agents" / "skills" / spec["name"] / "SKILL.md").relative_to(root)))

        for nm in command_names(spec):
            for folder, key in (
                (root / ".cursor" / "commands", "cursor_commands"),
                (root / ".claude" / "commands", "claude_commands"),
                (root / ".agents" / "commands", "codex_skills"),
            ):
                cmd = folder / f"{nm}.md"
                cmd.parent.mkdir(parents=True, exist_ok=True)
                cmd.write_text(_render_command_md(spec, nm), encoding="utf-8")
                if key != "codex_skills":
                    installed[key].append(str(cmd.relative_to(root)))

    _prune_retired_skill_dirs(root)
    _prune_retired_commands(root)
    from .skill_registry import write_registry_files

    write_registry_files(root, SKILL_SPECS)

    try:
        from .route_bank import packaged_bank_path, rebuild_packaged_bank, sync_project_bank

        # 已有打包库则只 sync，避免每次 install 重蒸脏 diff；缺文件才 rebuild
        if not packaged_bank_path().is_file():
            rebuild_packaged_bank()
        sync_project_bank(root)
        installed["agent_docs"].append(".memory-art/route_bank/route_bank.jsonl")
    except Exception as exc:  # noqa: BLE001 — 技能文件已写完；话术库失败单独提示，不虚标已装
        if not quiet:
            print(f"⚠️  route_bank 同步失败（技能已安装，请手动 python3 pmem_art.py route --rebuild）：{exc}")

    # 4. Upsert CLAUDE.md and AGENTS.md
    claude_md = root / "CLAUDE.md"
    _upsert_markdown_block(claude_md, "CLAUDE.md — Project Instructions")
    installed["agent_docs"].append("CLAUDE.md")

    agents_md = root / "AGENTS.md"
    _upsert_markdown_block(agents_md, "AGENTS.md — Codex & Coding Agent Instructions")
    installed["agent_docs"].append("AGENTS.md")

    # Keep Cursor alwaysApply rule in sync (not covered by skill folders alone).
    rules_dir = root / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rules_mdc = rules_dir / "pmem-art.mdc"
    rules_mdc.write_text(
        "---\n"
        "description: pmem-art 美术记忆与斜杠技能（与 CLAUDE.md / AGENTS.md 同步）\n"
        "alwaysApply: true\n"
        "---\n\n"
        + _render_agent_doc_block().replace(AGENT_DOC_MARKER_START + "\n", "").replace(
            "\n" + AGENT_DOC_MARKER_END, ""
        )
        + "\n",
        encoding="utf-8",
    )
    installed["agent_docs"].append(".cursor/rules/pmem-art.mdc")

    if not quiet:
        print(f"✨ 已自动安装 pmem-art {len(SKILL_SPECS)} 项美术技能（每个技能一个 /pmem- 入口）到 Cursor / Claude Code / Codex：")
        for spec in SKILL_SPECS:
            print(f"   · /{spec['name']:<18} — {spec['title']}")
        print("   · 安装路径: .cursor/{skills,commands}/ · .claude/{skills,commands}/ · .agents/skills/ · CLAUDE.md · AGENTS.md · .cursor/rules/pmem-art.mdc")
    return installed


_OWNED_SKILL_PREFIXES = ("pmem-", "art-", "source-command-pmem-", "source-command-art-")


def _prune_retired_commands(root: Path) -> None:
    """Delete slash commands that are no longer a /pmem- skill."""
    keep = {spec["name"] for spec in SKILL_SPECS}
    for folder in (
        root / ".cursor" / "commands",
        root / ".claude" / "commands",
        root / ".agents" / "commands",
    ):
        if not folder.exists():
            continue
        for child in list(folder.glob("*.md")):
            if child.stem.startswith(_OWNED_SKILL_PREFIXES) and child.stem not in keep:
                child.unlink()


def _prune_retired_skill_dirs(root: Path) -> None:
    """Drop skill folders that are no longer their own contract."""
    keep = {spec["name"] for spec in SKILL_SPECS}
    for base in (root / ".cursor" / "skills", root / ".claude" / "skills", root / ".agents" / "skills"):
        if not base.exists():
            continue
        for child in list(base.iterdir()):
            if not child.is_dir() or child.name in keep:
                continue
            if child.name.startswith(_OWNED_SKILL_PREFIXES):
                shutil.rmtree(child)


