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
    "1",
    "--image",
    "assets/skill_20261112_suite/out/ui.kit/r1.png",
    "--dims",
    "构图8.4/光影8.6/透视8.2/质感8.4/风格8.2/无瑕疵7.9",
    "--strengths",
    "已是主菜单而非Design三选一：中下黄PLAY一眼最大；顶栏圆角白胶囊厚蓝描边与场景同系软光泽；港湾窗景+吧台师脸在PLAY上方留空",
    "--defects",
    "顶栏数字72/85/233/1870与垫图资源值几乎同款回声；底栏只剩居中home落在大片米黄空带，导航壳偏空像未完成；PLAY下无Level副文案层次略薄",
    "--next-fix",
    "改掉垫图同款资源数字与图标排版回声；底栏补2～4枚轻量同系圆角入口且Home仍居中勿套RM五Tab；PLAY下加细Level条；保留港湾窗与吧台师脸周留空",
    "--conversation",
    "suite_ui_kit",
]
out_path = OUT / "06_judge1.out.txt"
err_path = OUT / "06_judge1.err.txt"
with out_path.open("w", encoding="utf-8") as fo, err_path.open("w", encoding="utf-8") as fe:
    p = subprocess.run(cmd, cwd=str(ROOT), stdout=fo, stderr=fe, text=True, encoding="utf-8")
print(out_path.read_text(encoding="utf-8", errors="replace"))
err = err_path.read_text(encoding="utf-8", errors="replace")
if err:
    print("ERR:", err)
print(f"EXIT={p.returncode}")
raise SystemExit(p.returncode)
