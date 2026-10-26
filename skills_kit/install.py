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

RATIONALITY_GATE = """
## 合理性（硬门槛）

合理性单独过关。风格分高，也不能把这格补过 9.6。

出图前按本技能要交付的对象关系自己组提示词。看这一张的像素再打分。没过就留下已经对的地方，下一轮点名没过的部位，只补那一句。第 2 轮起垫目前分数最高的那张，比它差的一轮不接着垫，也不把前几轮的修正叠进同一段。

有参考图时，先跑 `python3 pmem_art.py ref-read <参考图路径>`，再写提示词。它说底是透明的，提示词里就不要出现黑底、深底、底板。用一块浅的空底放下物件，这块浅底不是风格。表面只写眼睛在参考图上看见的那一句，同一组每一张、后面每一轮都用这同一句，不换成另一种媒介。小高光不要写成油亮、光面、发亮。表面光洁，也不要改成毛毡、纸纹或粗颗粒。同一张图继续修时，垫目前分数最高的那张成图，只改点名的那一处。第一张对一下底和表面。更油、更黑或更毛，就改提示词里这几个词，再出这一张。表面那一句已经对了，就留着。

对象关系：
- 人物、场景、图标：身体、透视、光和物件之间说得通。
- UI：标题、说明、按钮指向同一件事。
- 合成梯：每一件单独落在一个同样大的正方形里，不把八件画进同一张。两件相同的这一档合成下一档，画面里仍然只有这一件。低档只比高档小一圈，最低档也要占到正方形的大半，最高档留一圈边，不顶出格子，也不能变成一组场景。沿档位零件变多或剪影更复杂。末档在格子里最大、零件最多。相邻两档不能是同一类。第一段先用文字定稿这八行，六条都过了再逐张出图核对，不看美术品质。第二段在过关的正方形上抬风格和质感；关系散了，美术分也不能过。
"""


def _render_skill_md(spec: dict[str, Any], command_name: str) -> str:
    return (
        f"---\n"
        f"name: {command_name}\n"
        f"description: {spec['description']}\n"
        f"---\n\n"
        f"{spec['body'].strip()}\n"
        f"{RATIONALITY_GATE}"
    )


def _render_command_md(spec: dict[str, Any], command_name: str) -> str:
    return (
        f"---\n"
        f"description: {spec['title']}（pmem-art）\n"
        f"---\n\n"
        f"{spec['body'].strip()}\n"
        f"{RATIONALITY_GATE}"
    )


AGENT_DOC_MARKER_START = "<!-- pmem-art:skills:start -->"
AGENT_DOC_MARKER_END = "<!-- pmem-art:skills:end -->"


def _render_agent_doc_block() -> str:
    return f"""{AGENT_DOC_MARKER_START}
## 🎨 pmem-art 美术记忆系统与内置斜杠技能（Skills）

本项目挂载了 **pmem-art**（面向 Cursor / Claude Code / Codex 的个人美术积累记忆与闭环自评生图系统）。

### 1. 内置快捷技能（在对话框直接输入 `/技能名` 即可触发）

| 技能指令 | 简短别名 | 用途说明 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | **【强制 8轮 ≥9.6 收敛】** 通用生图：纯文本或垫图 → 生1张→打分挑刺→展示不足/改点→`<9.6`叠加修正→满8轮挑最高分→评分履历可见 |
| **`/pmem-ui`** | **`/art-ui`** | **【强制 8轮 ≥9.6 收敛】** SpriteCook 式 UI Kit/HUD/九宫格：概念先行→组件表→9-slice→状态族 |
| **`/pmem-concept`** | **`/art-concept`** | **【强制 8轮 ≥9.6 收敛】** 原画/概念图/Key Art（ZHO·FLUX 完整句 Prompt）— **与 draw 同等强制闭环，禁止只生一张** |
| **`/pmem-icon`** | **`/art-icon`** | **【强制 8轮 ≥9.6 收敛】** jezweb 式一致化 SVG 图标集：style-spec→分批→preview；关键枚强制收敛 |
| **`/pmem-style-lock`** | **`/art-style`** | **样张一键提炼风格圣经与色板锁定**：丢入样张提取 HEX 色板、光影笔触与禁用词，锁定进项目记忆 |
| **`/pmem-critique`** | **`/art-check`** | **主美级五维审稿与红线入库**：对照项目记忆给图片打分挑刺，并将翻车点记入 `style_redline` |
| **`/pmem-variant`** | **`/art-variant`** | **跨画风分叉与表情/动作差分**：继承角色核心锚点，派生水彩/Q版/像素子模块或序列帧差分 |
| **`/pmem-atlas`** | **`/art-map`** | **一键整理散图并刷新 `art-atlas.html` 可视化图谱** |
| **`/pmem-improve`** | **`/art-improve`** | **【进阶 peek】** 自我迭代报告（日常 finish 已静默跑） |
| **`/pmem-coach`** | **`/art-coach`** | **【进阶 peek】** 能力教练练习计划 |
| **`/pmem-learn`** | **`/art-learn`** | **【进阶 peek】** 知识广度建议（finish 已静默 enqueue） |
| **`/pmem-merge-ladder`** | **`/art-merge`** | **【两段各最多 8 轮】** 先用文字定稿合成关系，过了再逐张出图核对；然后在这些正方形上抬美术。每一件单独一个正方形，两两相合。相邻档只大一点。风格：写下的优先，否则跟参考图，都没有用默认质感好的卡通可爱。关系散了不能过 |
| **`/pmem-lens-propose`** | — | **镜头包提案**：参考图 → 多套具体 camera/light/props 包，用户选后再写入 goal / recompose_dir（不打 Absolute-5D 分） |

### 2. 评分履历可见 · 记忆静默写入（默认）
- 闭环每轮须向用户展示：五维分、不足、下一轮改点；`converge finish` 默认打印全轮评分履历并写记忆（`--no-apply` 可跳过；只要终稿加 `--quiet`）。
- `finish` / 高信号 `feedback` 后仍自动写反思、更新 taste、强化 recipe/红线、悄悄排队 learn——**不要**旁白记忆写入；最多转述一行「小提示」。
- 教练 / 广度报告用进阶技能 `/pmem-improve` · `/pmem-coach` · `/pmem-learn`。

### 3. 日常自然语言反馈沉淀（无需手写 YAML）
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
    - Codex / Agents Skills+Commands: .agents/skills/<name>/SKILL.md, .agents/commands/<name>.md, AGENTS.md
    """
    installed: dict[str, list[str]] = {
        "cursor_skills": [],
        "cursor_commands": [],
        "claude_skills": [],
        "claude_commands": [],
        "codex_skills": [],
        "codex_commands": [],
        "agent_docs": [],
    }

    for spec in SKILL_SPECS:
        names = [spec["name"], spec["alias"]]
        for nm in names:
            # 1. Cursor skill & slash command
            c_skill = root / ".cursor" / "skills" / nm / "SKILL.md"
            c_skill.parent.mkdir(parents=True, exist_ok=True)
            c_skill.write_text(_render_skill_md(spec, nm), encoding="utf-8")
            installed["cursor_skills"].append(str(c_skill.relative_to(root)))

            c_cmd = root / ".cursor" / "commands" / f"{nm}.md"
            c_cmd.parent.mkdir(parents=True, exist_ok=True)
            c_cmd.write_text(_render_command_md(spec, nm), encoding="utf-8")
            installed["cursor_commands"].append(str(c_cmd.relative_to(root)))

            # 2. Claude Code skill & slash command
            cl_skill = root / ".claude" / "skills" / nm / "SKILL.md"
            cl_skill.parent.mkdir(parents=True, exist_ok=True)
            cl_skill.write_text(_render_skill_md(spec, nm), encoding="utf-8")
            installed["claude_skills"].append(str(cl_skill.relative_to(root)))

            cl_cmd = root / ".claude" / "commands" / f"{nm}.md"
            cl_cmd.parent.mkdir(parents=True, exist_ok=True)
            cl_cmd.write_text(_render_command_md(spec, nm), encoding="utf-8")
            installed["claude_commands"].append(str(cl_cmd.relative_to(root)))

            # 3. Codex (.agents/skills/<nm>/SKILL.md + commands mirror for parity)
            cx_skill = root / ".agents" / "skills" / nm / "SKILL.md"
            cx_skill.parent.mkdir(parents=True, exist_ok=True)
            cx_skill.write_text(_render_skill_md(spec, nm), encoding="utf-8")
            installed["codex_skills"].append(str(cx_skill.relative_to(root)))

            cx_cmd = root / ".agents" / "commands" / f"{nm}.md"
            cx_cmd.parent.mkdir(parents=True, exist_ok=True)
            cx_cmd.write_text(_render_command_md(spec, nm), encoding="utf-8")
            installed.setdefault("codex_commands", []).append(str(cx_cmd.relative_to(root)))

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
        print(f"✨ 已自动安装 pmem-art {len(SKILL_SPECS)} 项美术技能（含别名共 {len(SKILL_SPECS)*2} 个斜杠入口）到 Cursor / Claude Code / Codex：")
        for spec in SKILL_SPECS:
            print(f"   · /{spec['name']:<16} (别名 /{spec['alias']:<11}) — {spec['title']}")
        print("   · 安装路径: .cursor/{skills,commands}/ · .claude/{skills,commands}/ · .agents/{skills,commands}/ · CLAUDE.md · AGENTS.md · .cursor/rules/pmem-art.mdc")
    return installed


