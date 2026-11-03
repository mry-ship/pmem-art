# -*- coding: utf-8 -*-
"""Generate L02-L06 for festival5 merge tracks via apikey-image."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMG = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-image\image_gen.py")
OUT = Path(__file__).resolve().parent

SURFACE = (
    "休闲merge软塑胶卡通，圆润倒角，饱和友好色，左上软光短接触影，光洁不油亮，浅空底；"
    "正方形单件居中，无脸无文字无等级字，不要黑底方框"
)

TRACKS = {
    "prize": {
        "base": "铜质圆章奖牌",
        "levels": {
            2: ("银边铜章", "铜质圆章奖牌加银质外环", "银质外环"),
            3: ("星心铜章", "铜质圆章奖牌银边中心浮雕星", "中心浮雕星"),
            4: ("桂叶铜章", "铜质圆章奖牌星心两侧月桂叶", "两侧月桂叶"),
            5: ("彩带铜章", "铜质圆章奖牌桂叶加红绸交叉带", "红绸交叉带"),
            6: ("宝石铜章", "铜质圆章奖牌彩带中心嵌宝石", "中心宝石"),
        },
    },
    "balloon": {
        "base": "绿气球",
        "levels": {
            2: ("结绳气球", "绿气球黄星底扎结绳", "底部扎结绳"),
            3: ("双星气球", "绿气球结绳加第二黄星", "第二颗黄星"),
            4: ("蝶结气球", "绿气球双星加粉小蝶结", "粉色小蝶结"),
            5: ("金箍气球", "绿气球蝶结加金色环箍", "金色环箍"),
            6: ("冠尖气球", "绿气球金箍顶冠尖", "顶冠尖"),
        },
    },
    "candy": {
        "base": "粉黄漩涡糖球",
        "levels": {
            2: ("扭结糖球", "粉黄漩涡糖球双端扭结糖纸", "双端扭结糖纸"),
            3: ("棍糖球", "粉黄漩涡糖球扭结下短糖棍", "短糖棍"),
            4: ("环箍糖球", "粉黄漩涡糖球棍糖赤道彩环", "赤道彩环"),
            5: ("蝶结糖球", "粉黄漩涡糖球环箍顶小蝶结", "顶小蝶结"),
            6: ("宝石糖球", "粉黄漩涡糖球蝶结中心糖宝石", "中心糖宝石"),
        },
    },
    "magic": {
        "base": "马戏条纹星球",
        "levels": {
            2: ("环带星球", "马戏条纹星球加赤道白环带", "赤道白环带"),
            3: ("侧星星球", "马戏条纹星球环带侧面小星贴", "侧面小星贴"),
            4: ("托环星球", "马戏条纹星球侧星底矮托环", "矮托环"),
            5: ("旗尖星球", "马戏条纹星球托环顶小三角旗", "顶小三角旗"),
            6: ("鼓饰星球", "马戏条纹星球旗尖两侧小圆鼓饰", "两侧小圆鼓饰"),
        },
    },
    "box": {
        "base": "紫布福袋",
        "levels": {
            2: ("金边福袋", "紫布福袋口沿金边", "口沿金边"),
            3: ("圆徽福袋", "紫布福袋金边正面圆徽", "正面圆徽"),
            4: ("流苏福袋", "紫布福袋圆徽加长流苏", "加长流苏"),
            5: ("绣带福袋", "紫布福袋流苏腰部绣带", "腰部绣带"),
            6: ("冠扣福袋", "紫布福袋绣带顶冠扣", "顶冠扣"),
        },
    },
}


def prompt_for(track: str, level: int) -> str:
    meta = TRACKS[track]
    name, sil, part = meta["levels"][level]
    scale = {2: "略大一圈", 3: "再大一圈", 4: "中等放大", 5: "明显更大", 6: "本链最大留边"}[level]
    return (
        f"Keep the same soft plastic casual merge-game icon style as the reference. "
        f"Single centered {meta['base']} upgrade: {name}. Silhouette: {sil}. "
        f"Only add this concrete part: {part}. Scale: {scale}. "
        f"{SURFACE}. Transparent or light empty background, square crop, no collage, no multiple items."
    )


def main() -> int:
    only = sys.argv[1:]  # optional: track names
    tracks = only or list(TRACKS)
    for track in tracks:
        ref = OUT / track / "L01.png"
        if not ref.exists():
            print(f"MISSING ref {ref}")
            return 1
        for level in range(2, 7):
            out = OUT / track / f"L{level:02d}.png"
            if out.exists() and out.stat().st_size > 1000:
                print(f"SKIP {out}")
                continue
            p = prompt_for(track, level)
            cmd = [
                sys.executable,
                str(IMG),
                "-o",
                str(out),
                "--size",
                "1024x1024",
                "--background",
                "transparent",
                "--image",
                str(ref),
                p,
            ]
            print(f"GEN {track} L{level:02d} ...")
            r = subprocess.run(cmd, cwd=str(ROOT))
            if r.returncode != 0:
                print(f"FAIL {track} L{level}")
                return r.returncode
            print(f"OK {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
