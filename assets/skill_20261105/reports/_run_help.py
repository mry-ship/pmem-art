import subprocess, sys
from pathlib import Path
root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
out = root / "assets/skill_20261105/reports/route_help.txt"
exe = Path(sys.executable)
py = exe.with_name("python.exe") if exe.name.lower() == "pythonw.exe" and exe.with_name("python.exe").exists() else exe
cmd = [str(py), "-u", str(root / "pmem_art.py"), "route", "--help"]
r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
out.write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
print("exit", r.returncode)
