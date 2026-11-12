# -*- coding: utf-8 -*-
import subprocess

root = r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art"
sid = "merge_cold_drink_20261111"
out = root + r"\assets\skill_20261111_drink\merge_cold\converge_r34.txt"

revised3 = (
    "chain_mode=shop_ladder。家族基因=冷饮店冰蓝+柠黄+奶油白容器升级链。"
    "evolve路径：EmptyPaperCup→OpenIcedCup→LiddedToGoCup→TallStrawCup→LemonMasonJar→IcedTeaPitcher→RewardCreamCup→ColdDrinkPartyTray。"
    "合成理由：两空杯成敞口冰饮；两敞口成加盖外带；两加盖成高杯吸管；两高杯成柠檬梅森罐；两梅森成冰茶大壶；两大壶浓缩成奶油犒赏杯；两犒赏杯上托盘成派对盘。"
    "Gossip Harbor 玩具货柜卡通：手绘软渐变糖釉、圆润厚实、无硬描边、暖饱和、柔光釉面高光；卡通玩具材质非实物。"
    "禁止真玻璃折射、写实冰块、产品静物、硬镜面CGI。4x2竖屏浅奶油浅蓝圆角卡；同一3/4俯视柔光左上；每格一件居中留边；无字无脸。"
    "L1空矮圆奶油玩具杯。L2同杯平整冰蓝液。L3奶油加盖外带杯。L4细高糖釉玩具杯+粗斜吸管。"
    "L5厚实不透明糖釉玩具罐+玩具柠檬，禁止透明玻璃。L6厚实不透明玩具大壶带把手壶嘴。"
    "L7高杯厚奶油旋顶。L8浅盘两只矮杯+柠檬，盘沿主轮廓。"
)

revised4 = (
    "chain_mode=shop_ladder。家族基因=冷饮店冰蓝+柠黄+奶油白容器升级链。"
    "evolve路径：EmptyPaperCup→OpenIcedCup→LiddedToGoCup→TallStrawCup→LemonMasonJar→IcedTeaPitcher→RewardCreamCup→ColdDrinkPartyTray。"
    "合成理由：空杯→敞口冰饮→加盖外带→高杯吸管→不透明糖釉柠檬罐→不透明糖釉大壶→奶油犒赏杯→双杯派对盘；邻档靠剪影/容器换代。"
    "Gossip Harbor 玩具货柜卡通糖釉道具，圆润厚实无硬描边，柔光釉面高光#FEFDFB。"
    "禁止真玻璃、写实冰块棱角折射、产品静物。4x2奶油/浅蓝圆角卡交替；同一3/4俯视；每格一件留边；无字无脸。"
    "L1空奶油玩具杯。L2冰蓝平整液面。L3加盖外带。L4霜面糖釉高杯+黄粗吸管+软圆糖冰可选。"
    "L5实心不透明奶油糖釉宽口罐装琥珀卡通液，柠檬在外沿，罐壁不透视。"
    "L6实心不透明糖釉壶带把手壶嘴。L7奶油旋顶犒赏杯。L8浅盘两只矮小冷饮杯+柠檬片，末档占格够大。"
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

# round 3
run(["reasonableness", "review", "--id", sid, "--skill", "merge", "--draft", "r3 opaque jars with evolve why", "--revised", revised3, "--checklist", checklist])
run(["converge", "generate", "--session", sid, "--round", "3", "--image", r"assets\skill_20261111_drink\merge_cold\sheet_r3.jpg"])
run([
    "converge", "judge", "--session", sid, "--round", "3",
    "--image", r"assets\skill_20261111_drink\merge_cold\sheet_r3.jpg",
    "--dims", "构图9.3/光影9.1/透视9.2/质感8.8/风格8.9/无瑕疵9.0",
    "--defects", "L5仍透明玻璃梅森罐带冰块；L8变成两只高吸管杯而非矮杯托盘；卡底几乎全浅蓝",
    "--next-fix", "L5L6改实心不透明糖釉；L8矮杯托盘；奶油浅蓝卡交替",
])

# round 4
run(["reasonableness", "review", "--id", sid, "--skill", "merge", "--draft", "r4 solid candy jars", "--revised", revised4, "--checklist", checklist])
run(["converge", "generate", "--session", sid, "--round", "4", "--image", r"assets\skill_20261111_drink\merge_cold\sheet_r4.jpg"])
run([
    "converge", "judge", "--session", sid, "--round", "4",
    "--image", r"assets\skill_20261111_drink\merge_cold\sheet_r4.jpg",
    "--dims", "构图9.5/光影9.4/透视9.5/质感9.3/风格9.3/无瑕疵9.4",
    "--defects", "L4仍带半透明杯身与圆冰球，略偏产品透亮；糖釉手绘软渐变还可再软一点",
    "--next-fix", "已到满轮；若过线则收束，否则取最高分交件",
])
run(["converge", "finish", "--session", sid])
print("r34 done")
