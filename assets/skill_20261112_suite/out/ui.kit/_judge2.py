# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
OUT = ROOT / "assets" / "skill_20261112_suite" / "out" / "ui.kit"
PY = sys.executable

cmd = [
    PY,
    "-u",
    str(ROOT / "pmem_art.py"),
    "converge",
    "judge",
    "--session",
    "suite_ui_kit",
    "--round",
    "2",
    "--image",
    "assets/skill_20261112_suite/out/ui.kit/r2.png",
    "--dims",
    "构图8.8/光影8.8/透视8.5/质感8.7/风格8.8/无瑕疵8.4",
    "--strengths",
    "资源值已换成18/42/1560/328摆脱垫图同款；PLAY下出现Level 12细进度条；底栏补齐Shop/Events/Home/Friends同系圆角格；港湾窗光与黄PLAY体积仍清楚",
    "--defects",
    "平视中景吧台师约占半身到腰，主光来自后方大窗而非灯笼；底栏四枚导致Home偏左非真正居中；顶栏最左变成星标18缺少等级圆环进度珠，等级语义被星标吞掉；底栏字重与顶栏厚描边体积略不齐",
    "--next-fix",
    "底栏改成奇数枚且Home绝对居中（推荐五槽或三槽）；顶栏恢复等级圆环进度珠并与星/币/宝石语义分开；底栏描边体积字重对齐顶栏胶囊；保留新资源数字与Level 12条与脸周留空",
    "--conversation",
    "suite_ui_kit",
]
out_path = OUT / "08_judge2.out.txt"
err_path = OUT / "08_judge2.err.txt"
with out_path.open("w", encoding="utf-8") as fo, err_path.open("w", encoding="utf-8") as fe:
    p = subprocess.run(cmd, cwd=str(ROOT), stdout=fo, stderr=fe, text=True, encoding="utf-8")
print(out_path.read_text(encoding="utf-8", errors="replace"))
err = err_path.read_text(encoding="utf-8", errors="replace")
if err:
    print("ERR:", err)
raise SystemExit(p.returncode)
