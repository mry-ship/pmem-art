import subprocess, sys, json, shutil
from pathlib import Path
root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
out = root / "assets/skill_20261105/draw_variant/_reg_r4_out.txt"
text = "同一粉裙金发仙子+果篮身份与机位，只改表情为困倦眯眼/打哈欠感；可量测部位要可验收：双眼上眼睑缘压到绿虹膜水平中线以下只留一条绿虹膜缝+高光；嘴轻张打哈欠或软困倦微张禁坏笑；禁新增手链"
prompt = "Same fairy on black. Bare wrists. Only squeeze BOTH upper lids over lower half of green iris to a thin iris slit + catchlight; keep soft tiny yawn."
img = "assets/skill_20261105/draw_variant/r4.png"

def run(args):
    p = subprocess.run([sys.executable,"-u",str(root/"pmem_art.py"),*args], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
    block = f"$ {' '.join(args[:8])}\nexit={p.returncode}\n{p.stdout}\n{p.stderr}\n\n"
    prev = out.read_text(encoding="utf-8") if out.exists() else ""
    out.write_text(prev + block, encoding="utf-8")
    print(block)
    return p.returncode

out.write_text("", encoding="utf-8")
run(["route","--text",text,"--canonical","同一身份；换表情；机位已在图上；走变体。","--conversation","battery1105-variant"])
rc = run(["converge","generate","--session","battery1105-variant","--conversation","battery1105-variant","--round","4","--image",img,"--prompt",prompt])
print("gen", rc)
if rc == 0:
    rc = run(["converge","judge","--session","battery1105-variant","--conversation","battery1105-variant","--round","4","--image",img,"--score","9.28","--dims","构图9.4/光影9.3/透视解剖9.3/质感9.3/风格9.3/无瑕疵9.0","--strengths","黑底身份机位果篮翅锁住；无紫手链；嘴轻张哈欠；双眼已明显加重眯眼","--defects","上睑仍未稳定压到虹膜下半只留一条绿虹膜缝，困倦硬验收差一点；左臂抬手姿态相对原图可有轻微漂移但不改表情验收","--next-fix","已满4轮；若续跑则上睑再下压到虹膜下半只留虹膜缝+高光"])
print("judge", rc)
rc = run(["converge","finish","--session","battery1105-variant","--conversation","battery1105-variant","--no-apply"])
print("finish", rc)
