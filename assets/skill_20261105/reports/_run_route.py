import subprocess, sys
from pathlib import Path
root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
out = root / "assets/skill_20261105/reports/route_ordinary.txt"
cmd = [
    sys.executable.replace("pythonw.exe", "python.exe").replace("pythonw", "python"),
    "-u",
    str(root / "pmem_art.py"),
    "route",
    "--text", "黑底蘑菇芝士果盘棚拍道具卡，垫图4，走普通图",
    "--canonical", "要画一张图；有参考；题材不变；走普通图",
]
# Prefer python.exe sibling of pythonw for capture
exe = Path(sys.executable)
if exe.name.lower() == "pythonw.exe":
    cand = exe.with_name("python.exe")
    if cand.exists():
        cmd[0] = str(cand)
r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
out.write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
print("exit", r.returncode, "bytes", out.stat().st_size)
