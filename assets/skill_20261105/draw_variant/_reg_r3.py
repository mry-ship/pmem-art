import subprocess, sys
from pathlib import Path
root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
out = root / "assets/skill_suite_20261105/draw_variant/_reg_r3_out.txt"
text = "同一粉裙金发仙子+果篮身份与机位，只改表情为困倦眯眼/打哈欠感；可量测部位要可验收：双眼上眼睑缘压到绿虹膜水平中线以下只留一条绿虹膜缝+高光；嘴轻张打哈欠或软困倦微张禁坏笑；禁新增手链"
prompt = "Same fairy on black, bare wrists. Only deepen BOTH upper lids past green iris midline to a thin iris slit + catchlight; keep soft tiny yawn; look to camera."
def run(args):
    p = subprocess.run([sys.executable,"-u",str(root/"pmem_art.py"),*args], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
    block = f"$ {' '.join(args[:8])}\nexit={p.returncode}\n{p.stdout}\n{p.stderr}\n\n"
    out.write_text((out.read_text(encoding='utf-8') if out.exists() else '') + block, encoding='utf-8')
    print(block)
    return p.returncode
out.write_text('', encoding='utf-8')
run(["route","--text",text,"--canonical","同一身份；换表情；机位已在图上；走变体。","--conversation","battery1105-variant"])
# try remapped path first
img = "assets/skill_20261105/draw_variant/r3.png"
if not (root/img).exists():
    img = "assets/skill_suite_20261105/draw_variant/r3.png"
rc = run(["converge","generate","--session","battery1105-variant","--conversation","battery1105-variant","--round","3","--image",img,"--prompt",prompt])
print('gen',rc)
if rc==0:
    rc = run(["converge","judge","--session","battery1105-variant","--conversation","battery1105-variant","--round","3","--image",img,"--score","9.16","--dims","构图9.3/光影9.3/透视解剖9.2/质感9.2/风格9.2/无瑕疵8.9","--strengths","黑底机位身份果篮翅锁住；无紫手链；嘴已轻张哈欠O型；有困倦半眯","--defects","上睑仍大约半闭到虹膜中线附近，未稳定盖过水平中线只留一条绿虹膜缝；困倦硬验收未完全兑现","--next-fix","做成明显眯眼：上睑缘压到虹膜下半，只留一条绿虹膜缝+高光；邻区发型衣饰果篮不动"])
print('judge',rc)
