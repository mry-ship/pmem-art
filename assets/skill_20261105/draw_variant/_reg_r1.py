import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).with_name("_reg_r1_out.txt")
text = (
    "同一粉裙金发仙子+果篮身份与机位，只改表情为困倦眯眼/打哈欠感；可量测部位要可验收："
    "双眼上眼睑缘压到绿虹膜水平中线以下只留一条绿虹膜缝+高光；嘴轻张打哈欠或软困倦微张禁坏笑；禁新增手链"
)
revised = (
    "Same identity and locked camera as the reference: medium close-up waist-up blonde fairy on solid black, "
    "slight three-quarter facing camera, cartoon 3D soft-plastic render. "
    "KEEP LOCKED: bright blonde thick side-swept bangs and twin braids with pink bands; pointed elf ears with pink inner tone; "
    "emerald green irises; pink puffed-sleeve dress with white collar and vertical pearl buttons; pearl necklace with one turquoise circular pendant; "
    "four translucent light-blue veined fairy wings; right hand (viewer left) holding woven fruit basket with red apple, green grapes, yellow fruit; "
    "left hand raised near chest; same head tilt and silhouette; no new accessories, no purple bracelet. "
    "ONLY CHANGE expression to sleepy/yawning: BOTH upper eyelids must press down past the horizontal midline of each green iris, "
    "leaving only a thin green iris slit plus catchlight; soft sleepy half-open mouth as a light yawn (not a smirk, not a wide grin). "
    "Keep soft plastic highlights, clean edges, commercial casual cute character finish. Solid black background."
)
Path(__file__).with_name("_revised_prompt.txt").write_text(revised, encoding="utf-8")


def run(args: list[str]) -> int:
    p = subprocess.run(
        [sys.executable, "-u", str(root / "pmem_art.py"), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    block = f"$ {' '.join(args[:8])}\nexit={p.returncode}\n{p.stdout}\n{p.stderr}\n\n"
    with out.open("a", encoding="utf-8") as f:
        f.write(block)
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
        "1",
        "--image",
        "assets/skill_20261105/draw_variant/r1.png",
        "--prompt",
        revised,
    ]
)
if rc != 0:
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
        "1",
        "--image",
        "assets/skill_20261105/draw_variant/r1.png",
        "--score",
        "9.05",
        "--dims",
        "构图9.4/光影9.2/透视解剖9.0/质感9.1/风格9.0/无瑕疵8.2",
        "--strengths",
        "黑底半身机位与粉裙金发尖耳果篮翅身份大体锁住；嘴已呈打哈欠开口",
        "--defects",
        "双眼上眼睑是否压到虹膜中线仍偏浅、右眼更开；右腕多出紫手链非点名改项；吊坠偏金圈不够青绿圆宝石；嘴角可更软困而非用力张大",
        "--next-fix",
        "双眼上睑继续下压到盖住虹膜水平中线只留一条绿虹膜缝+高光；去掉紫手链；吊坠改回青绿圆形；嘴改软困倦轻哈欠",
    ]
)
sys.exit(rc)
