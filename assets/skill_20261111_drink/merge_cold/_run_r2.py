# -*- coding: utf-8 -*-
import subprocess

root = r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art"
sid = "merge_cold_drink_20261111"
img = r"assets\skill_20261111_drink\merge_cold\sheet_r2.jpg"
out = root + r"\assets\skill_20261111_drink\merge_cold\converge_r2.txt"

revised = (
    "chain_mode=shop_ladder。"
    "Gossip Harbor 玩具货柜卡通：手绘软渐变糖釉道具、圆润厚实、无硬描边、暖饱和、柔光釉面高光#FEFDFB、棋盘缩略可认；"
    "材质锁死卡通玩具/糖釉货柜道具，不是实物，也不是硬镜面CGI。"
    "禁止写实摄影、美食棚拍、产品静物、玻璃真实折射、写实冰块、木纹指纹、果汁乳浊摄影感、微距毛孔、油光金属、硬镜面3D。"
    "整表统一：同一3/4俯视、同一柔光左上、浅奶油浅蓝圆角卡、冰蓝+柠黄+奶油白色相；每格一件居中留边；无字无脸。"
    "L1空纸杯矮圆玩具杯无液无盖无吸管。"
    "L2同形矮圆杯装平整冰蓝卡通液面无盖无吸管。"
    "L3矮圆奶油色加盖外带玩具杯盖顶小口无吸管。"
    "L4细高厚实半透明糖釉玩具杯斜出粗玩具吸管，禁止真玻璃。"
    "L5宽口厚实不透明糖釉玩具梅森罐装琥珀色卡通冰茶加一片玩具柠檬，禁止透明玻璃与写实冰。"
    "L6带把手壶嘴的厚实糖釉玩具大壶装同色卡通冰茶，禁止真玻璃。"
    "L7高杯厚奶油旋顶加柠黄装饰单杯犒赏。"
    "L8浅托盘两只小冷饮杯加柠檬片，盘沿主轮廓，末档占格不矮于前档。"
    "邻档靠剪影或容器可分。一眼失败：真玻璃折射、写实冰块、切顶残片、有字有脸。"
)
checklist = (
    "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;"
    "single_centered_item=ok;chain_mode_declared=ok;upgrade_reason_concrete=ok;"
    "family_or_base_lock=ok;sheet_safe_zone=ok"
)

def run(args):
    with open(out, "a", encoding="utf-8") as f:
        f.write("\n>>> " + " ".join(args[:6]) + "\n")
        r = subprocess.run(["py", "-3", "-u", "pmem_art.py"] + args, cwd=root, stdout=f, stderr=subprocess.STDOUT)
        f.write(f"EXIT={r.returncode}\n")
    return r.returncode

open(out, "w", encoding="utf-8").write("")
run(["reasonableness", "review", "--id", sid, "--skill", "merge", "--draft", "r2 cold drink sheet restart toy glaze", "--revised", revised, "--checklist", checklist])
run(["converge", "generate", "--session", sid, "--round", "2", "--image", img])
run([
    "converge", "judge", "--session", sid, "--round", "2", "--image", img,
    "--dims", "构图9.4/光影9.2/透视9.3/质感8.9/风格9.0/无瑕疵9.1",
    "--defects", "L5梅森罐与L6大壶仍是透明真玻璃感并带写实冰块；L4液色偏奶油偏离冰蓝家族；L8托盘占格仍偏小",
    "--next-fix", "纯文重开不垫上轮：L5L6改成厚实不透明糖釉玩具罐壶，去掉真玻璃与冰块；L4液面改冰蓝；L8托盘加大占格与前档齐平",
])
print("r2 done")
