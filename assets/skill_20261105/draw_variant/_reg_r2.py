import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).with_name("_reg_r2_out.txt")
text = (
    "同一粉裙金发仙子+果篮身份与机位，只改表情为困倦眯眼/打哈欠感；可量测部位要可验收："
    "双眼上眼睑缘压到绿虹膜水平中线以下只留一条绿虹膜缝+高光；嘴轻张打哈欠或软困倦微张禁坏笑；禁新增手链"
)
prompt = (
    "Same locked blonde pink-dress fairy identity and camera as reference on solid black. "
    "BARE wrists, no bracelet. Turquoise circular pendant. "
    "ONLY expression: BOTH upper eyelids pressed BELOW green iris midline (thin iris slit + catchlight); "
    "soft light yawn mouth. Round2 fix after shallow lids and bracelet."
)


def run(args):
    p = subprocess.run(
        [sys.executable, "-u", str(root / "pmem_art.py"), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    block = f"$ {' '.join(args[:8])}\nexit={p.returncode}\n{p.stdout}\n{p.stderr}\n\n"
    out.write_text(out.read_text(encoding="utf-8") + block if out.exists() else block, encoding="utf-8")
    print(block)
    return p.returncode


out.write_text("", encoding="utf-8")
run(
    [
        "route",
        "--text",
        text,
        "--canonical",
        "同一身份；换表情；机位已在图上；走变体。",
        "--conversation",
        "battery1105-variant",
    ]
)
rc = run(
    [
        "converge",
        "generate",
        "--session",
        "battery1105-variant",
        "--conversation",
        "battery1105-variant",
        "--round",
        "2",
        "--image",
        "assets/skill_20261105/draw_variant/r2.png",
        "--prompt",
        prompt,
    ]
)
if rc:
    sys.exit(rc)
rc = run(
    [
        "converge",
        "judge",
        "--session",
        "battery1105-variant",
        "--conversation",
        "battery1105-variant",
        "--round",
        "2",
        "--image",
        "assets/skill_20261105/draw_variant/r2.png",
        "--score",
        "9.00",
        "--dims",
        "构图9.0/光影9.2/透视解剖9.0/质感9.2/风格9.1/无瑕疵8.7",
        "--strengths",
        "紫手链已去掉；青绿圆吊坠更接近；黑底身份与果篮翅大体锁住；有困倦半眯",
        "--defects",
        "上睑仍大约只到虹膜上1/3~中线附近，未稳定盖过水平中线只留虹膜缝；嘴偏闭合浅笑缺少轻哈欠微张；视线略下偏相对原图机位",
        "--next-fix",
        "做成明显眯眼：上睑缘压到虹膜下半只留一条绿虹膜缝+高光；嘴轻张软困哈欠；视线与头倾回到原图对镜头",
    ]
)
sys.exit(rc)
