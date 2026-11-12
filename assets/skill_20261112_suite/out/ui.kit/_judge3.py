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
    "3",
    "--image",
    "assets/skill_20261112_suite/out/ui.kit/r3.png",
    "--dims",
    "构图9.2/光影9.1/透视8.9/质感9.1/风格9.2/无瑕疵8.8",
    "--strengths",
    "顶栏已恢复圆环等级珠LEVEL 18并与42/1560/328资源分家；底栏五槽Home居中；PLAY+Level12条层次清楚；港湾窗光与吧台师脸周仍留空",
    "--defects",
    "平视中景，吧台师约半身，主光仍是后方大窗；等级圆环内LEVEL字与18挤在一起字重发糊；底栏五槽标签偏小且描边体积仍略薄于顶栏胶囊；Brimwave与Cafe两行色差略跳",
    "--next-fix",
    "等级珠只放大号18+细进度环，LEVEL小字移到环外或去掉；底栏标签加粗并加同系厚描边体积投影对齐顶栏；统一标题Brimwave Cafe为同一套描边高光；其余锁定不动",
    "--conversation",
    "suite_ui_kit",
]
out_path = OUT / "10_judge3.out.txt"
err_path = OUT / "10_judge3.err.txt"
with out_path.open("w", encoding="utf-8") as fo, err_path.open("w", encoding="utf-8") as fe:
    p = subprocess.run(cmd, cwd=str(ROOT), stdout=fo, stderr=fe, text=True, encoding="utf-8")
text = out_path.read_text(encoding="utf-8", errors="replace")
print(text)
err = err_path.read_text(encoding="utf-8", errors="replace")
if err:
    print("ERR:", err)
raise SystemExit(p.returncode)
