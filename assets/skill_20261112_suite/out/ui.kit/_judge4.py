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
    "4",
    "--image",
    "assets/skill_20261112_suite/out/ui.kit/r4.png",
    "--dims",
    "构图9.4/光影9.3/透视9.1/质感9.3/风格9.4/无瑕疵9.0",
    "--strengths",
    "相对r3：等级珠大号18更清楚、五槽Home仍居中、PLAY+Level12与港湾窗光/吧台师脸周留空保持；顶栏资源42/1560/328与软光泽蓝描边胶囊齐套",
    "--defects",
    "平视中景半身吧台师，主光仍是后方大窗；等级环内仍塞着LEVEL小字未完全外移；Cafe一行色比Brimwave偏奶油跳色；底栏槽描边体积仍略薄于顶栏胶囊",
    "--next-fix",
    "已满4轮取最高分；若续跑只外移LEVEL字并统一标题描边高光、加厚底栏体积",
    "--conversation",
    "suite_ui_kit",
]
out_path = OUT / "12_judge4.out.txt"
err_path = OUT / "12_judge4.err.txt"
with out_path.open("w", encoding="utf-8") as fo, err_path.open("w", encoding="utf-8") as fe:
    p = subprocess.run(cmd, cwd=str(ROOT), stdout=fo, stderr=fe, text=True, encoding="utf-8")
print(out_path.read_text(encoding="utf-8", errors="replace"))
err = err_path.read_text(encoding="utf-8", errors="replace")
if err:
    print("ERR:", err)
raise SystemExit(p.returncode)
