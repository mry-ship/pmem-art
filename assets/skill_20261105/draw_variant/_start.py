import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).with_name("_start_out.txt")
goal = (
    "同一粉裙金发仙子+果篮身份与机位，只改表情为困倦眯眼/打哈欠感；可量测部位要可验收："
    "双眼上眼睑缘压到绿虹膜水平中线以下只留一条绿虹膜缝+高光；嘴轻张打哈欠或软困倦微张禁坏笑；禁新增手链"
)
route_text = goal
canonical = "同一身份；换表情；机位已在图上；走变体。"

# 1) bind route to conversation with goal-aligned text
route_cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "route",
    "--text",
    route_text,
    "--canonical",
    canonical,
    "--conversation",
    "battery1105-variant",
]
r1 = subprocess.run(route_cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")

# 2) start converge
start_cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "converge",
    "start",
    "--session",
    "battery1105-variant",
    "--conversation",
    "battery1105-variant",
    "--route-id",
    "draw.variant",
    "--module",
    "character.FairyPink",
    "--mode",
    "quality",
    "--scale",
    "low",
    "--threshold",
    "9.5",
    "--max-rounds",
    "4",
    "--aspect-ratio",
    "1:1",
    "--ref-image",
    "assets/skill_20261103/02_character.png",
    "--reference-image-paths",
    "assets/skill_20261103/02_character.png",
    "--goal",
    goal,
    "--ref-analysis",
    (
        "构图：正中近景半身，略俯视正面微侧；黑实底。"
        "姿态：右手(观众左)提藤编果篮(红苹果/绿葡萄/黄果)，左手(观众右)抬至胸前；双肩平，头略倾。"
        "身份锚：金发厚刘海+双辫粉结；翠绿大瞳；尖耳粉内廓；粉泡袖连衣裙白领珍珠排扣；"
        "珍珠链青绿圆形吊坠；四片半透明淡蓝翅脉。"
        "表情原态：双眼全睁、露齿微笑。"
        "色板：#F4D36A金发 #7BC24A绿瞳 #F3A7C3粉裙 #E8F6FF翅 #1A1A1A底。"
        "笔触：干净卡通3D软塑胶高光。可改唯表情；机位/剪影/道具/配饰全锁。"
        "红线：上睑须压过虹膜中线；禁紫手链；嘴勿坏笑。"
    ),
]
r2 = subprocess.run(start_cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
out.write_text(
    f"route_exit={r1.returncode}\nROUTE_STDOUT:\n{r1.stdout}\nROUTE_STDERR:\n{r1.stderr}\n\n"
    f"start_exit={r2.returncode}\nSTART_STDOUT:\n{r2.stdout}\nSTART_STDERR:\n{r2.stderr}\n",
    encoding="utf-8",
)
print(out.read_text(encoding="utf-8"))
sys.exit(0 if r2.returncode == 0 else r2.returncode)
