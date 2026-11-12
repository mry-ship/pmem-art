# -*- coding: utf-8 -*-
import subprocess
import sys

root = r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art"
sid = "merge_cold_drink_20261111"
img = r"assets\skill_20261111_drink\merge_cold\sheet_r1.jpg"
prompt = open(
    root + r"\assets\skill_20261111_drink\merge_cold\prompt_r1.txt",
    encoding="utf-8",
).read()
out = root + r"\assets\skill_20261111_drink\merge_cold\converge_r1.txt"

def run(args):
    cmd = ["py", "-3", "-u", "pmem_art.py"] + args
    with open(out, "a", encoding="utf-8") as f:
        f.write("\n>>> " + " ".join(args[:6]) + "…\n")
        r = subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT)
        f.write(f"\nEXIT={r.returncode}\n")
    return r.returncode

open(out, "w", encoding="utf-8").write("")
c1 = run([
    "converge", "generate",
    "--session", sid,
    "--round", "1",
    "--image", img,
    "--prompt", prompt,
])
c2 = run([
    "converge", "judge",
    "--session", sid,
    "--round", "1",
    "--image", img,
    "--dims", "构图9.3/光影9.0/透视9.2/质感8.7/风格8.5/无瑕疵9.0",
    "--defects", "L4-L6玻璃与冰块偏产品静物写实；糖釉玩具高光不足；整体偏干净产品3D而非Gossip Harbor货柜卡通",
    "--next-fix", "整张重开：所有容器改厚实糖釉玩具材质，禁止真实玻璃折射与写实冰块；液面用卡通色块；保持L1-L8剪影与4x2版式",
])
sys.exit(0 if c1 == 0 and c2 == 0 else 1)
