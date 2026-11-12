# -*- coding: utf-8 -*-
import subprocess

root = r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art"
sid = "merge_cold_drink_20261111"
img = r"assets\skill_20261111_drink\merge_cold\sheet_r3.jpg"
out = root + r"\assets\skill_20261111_drink\merge_cold\converge_r3.txt"

revised = (
    "chain_mode=shop_ladder。"
    "Gossip Harbor 玩具货柜卡通：手绘软渐变糖釉道具、圆润厚实、无硬描边、暖饱和、柔光釉面高光、棋盘缩略可认。"
    "材质锁死卡通玩具糖釉，不是实物，禁止真玻璃折射、写实冰块、产品静物、硬镜面CGI。"
    "4x2竖屏浅奶油与浅蓝圆角卡交替；同一3/4俯视柔光左上；冰蓝+柠黄+奶油白；每格一件居中留边；无字无脸。"
    "L1空矮圆奶油玩具杯。"
    "L2同杯平整冰蓝卡通液面。"
    "L3奶油加盖外带玩具杯。"
    "L4细高半透明糖釉玩具杯+粗斜吸管+冰蓝液，可用软圆糖冰块但禁止真冰折射。"
    "L5关键点：宽口厚实不透明奶油或琥珀糖釉玩具罐，罐壁实心不透、内侧贴一片玩具柠檬，液面卡通琥珀色，绝对禁止透明玻璃罐。"
    "L6关键点：厚实不透明糖釉玩具大壶带把手壶嘴，实心罐身，禁止透明玻璃。"
    "L7高杯厚奶油旋顶+柠檬装饰。"
    "L8浅盘托两只矮小冷饮杯+柠檬片，盘沿主轮廓，占格够大。"
    "一眼失败：透明玻璃罐壶、写实冰块棱角、切顶残片、有字有脸。"
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
run(["reasonableness", "review", "--id", sid, "--skill", "merge", "--draft", "r3 opaque candy jars", "--revised", revised, "--checklist", checklist])
run(["converge", "generate", "--session", sid, "--round", "3", "--image", img])
run([
    "converge", "judge", "--session", sid, "--round", "3", "--image", img,
    "--dims", "构图9.3/光影9.1/透视9.2/质感8.8/风格8.9/无瑕疵9.0",
    "--defects", "L5仍是透明玻璃梅森罐带写实感冰块；L4/L8仍偏透亮产品杯；卡底几乎全浅蓝缺少奶油交替；糖釉手绘感不足",
    "--next-fix", "第4轮纯文重开：L5L6必须实心不透明糖釉玩具罐壶；去掉透明玻璃；L8改矮杯托盘；奶油浅蓝卡交替；更软糖釉高光",
])
print("r3 done")
