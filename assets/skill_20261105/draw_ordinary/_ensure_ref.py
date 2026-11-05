# -*- coding: utf-8 -*-
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[3]
dst = root / "assets/skill_20261103/04_prop.png"
local = Path(__file__).with_name("ref_04_prop.png")
candidates = [
    local,
    root / "assets/skill_20261103/04_prop.png",
    Path(r"C:\Users\ZhengLangPC\AppData\Local\Temp\pmem-art-update-0165\extract\pmem-art-0.16.5-art\assets\skill_20261103\04_prop.png"),
    Path(r"C:\Users\ZhengLangPC\AppData\Local\Temp\pmem-art-update-0164\extract\pmem-art-0.16.4-art\assets\skill_20261103\04_prop.png"),
]
src = next((p for p in candidates if p.exists()), None)
if src is None:
    raise SystemExit("no 04_prop.png source")
dst.parent.mkdir(parents=True, exist_ok=True)
if not dst.exists() or dst.stat().st_size != src.stat().st_size:
    shutil.copy2(src, dst)
if not local.exists():
    shutil.copy2(src, local)
print("ref_ok", dst, dst.stat().st_size)
