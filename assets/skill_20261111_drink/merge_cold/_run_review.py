# -*- coding: utf-8 -*-
import subprocess
import sys

draft = "冷饮合成梯整表草稿：一组饮料八档。"
revised = (
    "chain_mode=shop_ladder。"
    "Gossip Harbor 玩具货柜卡通：光泽卡通3D、圆润厚实、无硬描边、暖饱和、柔光渐变、糖釉玩具高光；"
    "材质是卡通玩具不是实物。禁止写实摄影、美食棚拍、产品静物、玻璃真实折射、木纹指纹、果汁乳浊摄影感。"
    "整表统一：同一3/4俯视、同一柔光左上、浅奶油浅蓝圆角卡、冰蓝+柠黄+奶油白色相家族；每格一件居中留边；无字无脸。"
    "L1 空纸杯：一只空的矮圆纸杯，无液无盖无吸管，杯口朝上可见内壁。"
    "L2 敞口冰饮：同形矮圆杯装满冰蓝饮料，可见平整液面，仍无盖无吸管。"
    "L3 加盖外带杯：矮圆外带杯加上圆盖，盖顶小口可见，液面被盖住，无吸管。"
    "L4 高杯吸管：细高透明玩具杯加一根斜出吸管，比矮圆杯更高，盖消失。"
    "L5 柠檬梅森罐：宽口梅森罐装满冰茶，罐侧可见柠檬片，吸管消失，罐肩更宽。"
    "L6 冰茶大壶：带把手与壶嘴的宽肩大壶装满冰茶，梅森螺纹罐口消失。"
    "L7 奶油犒赏杯：高杯特饮顶着厚奶油旋顶与柠黄装饰，壶嘴把手消失，单杯犒赏。"
    "L8 冷饮派对盘：浅托盘上两只小冷饮杯并柠檬片，盘沿是主轮廓，仍是一件货并留边。"
    "禁止跨格拼贴、残片、切顶；邻档靠剪影或容器可分，不靠放大。"
    "一眼失败：写实棚拍、邻档同剪影、切顶残片、黑整表底、有字有脸。"
    "约束：不改机位；不增删主体清单；禁止回落写实棚拍。"
)
checklist = (
    "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;"
    "single_centered_item=ok;chain_mode_declared=ok;upgrade_reason_concrete=ok;"
    "family_or_base_lock=ok;sheet_safe_zone=ok"
)
root = r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art"
cmd = [
    "py",
    "-3",
    "-u",
    "pmem_art.py",
    "reasonableness",
    "review",
    "--id",
    "merge_cold_drink_20261111",
    "--skill",
    "merge",
    "--draft",
    draft,
    "--revised",
    revised,
    "--checklist",
    checklist,
]
out = root + r"\assets\skill_20261111_drink\merge_cold\reason_out.txt"
with open(out, "w", encoding="utf-8") as f:
    r = subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT)
sys.exit(r.returncode)
