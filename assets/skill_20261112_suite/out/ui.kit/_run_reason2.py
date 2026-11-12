# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
OUT = ROOT / "assets" / "skill_20261112_suite" / "out" / "ui.kit"
PY = sys.executable

draft = "Brimwave Cafe main menu HUD soft glossy casual UI 9:16"
revised = (
    "Mobile 9:16 casual-merge MAIN MENU HUD concept for Brimwave Cafe "
    "(NOT a Design renovation picker screen). Full-bleed warm harbor cafe interior scene under "
    "soft afternoon window light: creamy wood counters, teal accents, pastry trays, coffee steam, "
    "distant harbor boats through big windows. Soft glossy toy-plastic casual UI chrome matching "
    "pad craft — do not copy pad pixel layout. "
    "顶栏单行资源条：等级珠/体力/金币/宝石，白底圆角胶囊，厚描边（蓝白描边），轻体积挤出，软接触投影，粗白数字深描边字重；"
    "右上小设置齿轮不抢主任务。中景港湾咖啡馆场景铺满，吧台师/吉祥物情绪锚，主按钮不遮脸、不压主角五官，脸周留空。"
    "中下主 CTA：超大软光泽 PLAY（或 Level）按钮，圆角厚描边、顶高光、底部接触影、字重最粗最大，一眼最大可点。"
    "可选轻量底栏 Home 居中（休闲 merge，非 PVP 大厅，非三消 RM 默认五 Tab）。"
    "可读标题 Brimwave Cafe。无乱码、无手机外框、无 Design 三选一条、无三消盘面。"
    "对标品类=休闲merge主菜单HUD（ui.casual_hud）：上架截图密度，chrome 与场景同系软光泽。"
)
checklist = (
    "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;"
    "layout_zones=ok;no_content_clutter=ok;chrome_not_illustration=ok;"
    "cta_clear_of_faces=ok;control_craft=ok"
)

cmd = [
    PY,
    "-u",
    str(ROOT / "pmem_art.py"),
    "reasonableness",
    "review",
    "--id",
    "suite_ui_kit",
    "--skill",
    "ui",
    "--draft",
    draft,
    "--revised",
    revised,
    "--checklist",
    checklist,
    "--notes",
    "concept-only; 对标品类=休闲merge主菜单HUD；垫图只锁chrome气质禁止像素抄构图；主按钮不遮脸；顶栏主钮写清描边体积投影字重",
]
out_path = OUT / "04_reason2.out.txt"
err_path = OUT / "04_reason2.err.txt"
with out_path.open("w", encoding="utf-8") as fo, err_path.open("w", encoding="utf-8") as fe:
    p = subprocess.run(cmd, cwd=str(ROOT), stdout=fo, stderr=fe, text=True, encoding="utf-8")
print(out_path.read_text(encoding="utf-8", errors="replace"))
err = err_path.read_text(encoding="utf-8", errors="replace")
if err:
    print("ERR:", err)
print(f"EXIT={p.returncode}")
raise SystemExit(p.returncode)
