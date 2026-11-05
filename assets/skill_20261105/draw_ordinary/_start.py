# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "converge",
    "start",
    "--session",
    "battery1105-ordinary",
    "--conversation",
    "battery1105-ordinary",
    "--route-id",
    "draw.ordinary",
    "--module",
    "prop.mushroom_cheese_platter",
    "--mode",
    "quality",
    "--scale",
    "medium",
    "--threshold",
    "9.5",
    "--max-rounds",
    "4",
    "--aspect-ratio",
    "1:1",
    "--medium-family",
    "立体",
    "--ref-image",
    "assets/skill_20261103/04_prop.png",
    "--reference-image-paths",
    "assets/skill_20261103/04_prop.png",
    "--goal",
    (
        "黑底棚拍休闲手游道具卡：毒蝇伞形蘑菇芝士果盘；蘑菇盖作盘面，上置瑞士芝士块与三角楔、"
        "泪滴蓝莓、橙红樱桃与绿叶；纯黑实色底；顶级休闲手游道具卡棚拍完成度；题材与参考不变，"
        "medium 锁机位；垫图4，走普通图"
    ),
    "--ref-analysis",
    (
        "构图：正侧略俯棚拍道具卡，主体居中偏下，干净剪影，纯黑实色底。"
        "机位：三分之四视角，蘑菇柄在下、伞盖作盘面。"
        "主体：红橙伞盖+乳白奶油圆斑+粗壮乳白菌柄；盘面左下瑞士芝士大方块叠三角楔（圆孔清晰）；"
        "前左+后右两颗泪滴形蓝莓；中右三颗橙红带蒂樱桃；右后三片亮绿叶撑高度。"
        "色板：#C43A1A红橙伞/#F5E6C8奶油斑柄/#E8C45A芝士/#2F6FB5蓝莓/#E85A2A樱桃/#3FA84A绿叶/#000000底。"
        "光影：顶柔棚光，宽柔高光，短接触AO影，无硬边射灯。"
        "材质：休闲手游软圆厚实半哑光3D道具，非写实食物摄影。"
        "必须继承：黑底、蘑菇盘身份、芝士/蓝莓/樱桃/绿叶配置与相对摆位、棚拍完成度。"
        "不要继承：任何文字、场景背景、竞品像素构图抄袭。"
    ),
]
proc = subprocess.run(
    cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace"
)
Path(__file__).with_name("_start_out.txt").write_text(
    f"exit={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n",
    encoding="utf-8",
)
sys.exit(proc.returncode)
