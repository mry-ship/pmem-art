# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
session = "battery1105-ordinary"
conv = "battery1105-ordinary"
image = "assets/skill_20261105/draw_ordinary/r1.png"


def run(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-u", str(root / "pmem_art.py"), *args]
    return subprocess.run(
        cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


# re-bind route for this conversation
b = run(
    [
        "route",
        "--text",
        (
            "黑底棚拍休闲手游道具卡：毒蝇伞形蘑菇芝士果盘；蘑菇盖作盘面，上置瑞士芝士块与三角楔、"
            "泪滴蓝莓、橙红樱桃与绿叶；纯黑实色底；顶级休闲手游道具卡棚拍完成度；题材与参考不变，"
            "medium 锁机位；垫图4，走普通图"
        ),
        "--canonical",
        "要画一张图；有参考；题材不变；走普通图",
        "--conversation",
        conv,
    ]
)
Path(__file__).with_name("_bind_before_r1.txt").write_text(
    f"exit={b.returncode}\n{b.stdout}\n{b.stderr}", encoding="utf-8"
)

g = run(
    [
        "converge",
        "generate",
        "--session",
        session,
        "--conversation",
        conv,
        "--route-id",
        "draw.ordinary",
        "--round",
        "1",
        "--image",
        image,
    ]
)
Path(__file__).with_name("_generate_r1.txt").write_text(
    f"exit={g.returncode}\nSTDOUT:\n{g.stdout}\nSTDERR:\n{g.stderr}\n",
    encoding="utf-8",
)
if g.returncode != 0:
    print(g.stdout)
    print(g.stderr)
    sys.exit(g.returncode)

j = run(
    [
        "converge",
        "judge",
        "--session",
        session,
        "--conversation",
        conv,
        "--round",
        "1",
        "--image",
        image,
        "--dims",
        "构图9.4/光影9.3/透视9.5/质感9.2/风格9.4/无瑕疵9.0",
        "--strengths",
        "黑底棚拍机位与蘑菇盘身份锁住；芝士叠块圆孔清晰；柔棚光短接触影整体可读",
        "--defects",
        "两颗蓝莓顶端多出小绿叶（参考无此叶）；伞盖奶油圆斑数量/分布偏少偏齐，不及参考饱满错落",
        "--next-fix",
        "去掉蓝莓顶小叶，只保留右后三片大绿叶；伞盖奶油圆斑按参考增密并错落排布，其余摆位机位不动",
    ]
)
Path(__file__).with_name("_judge_r1.txt").write_text(
    f"exit={j.returncode}\nSTDOUT:\n{j.stdout}\nSTDERR:\n{j.stderr}\n",
    encoding="utf-8",
)
print(j.stdout)
sys.exit(j.returncode)
