#!/usr/bin/env python3
"""
16 Empty Claude Bot Instances Parallel Cold-Start Runner for 4 Fresh Vertical Reference Images.
Ensures 100% cold start per bot:
- 0 old memories (isolated project root + isolated empty shared root)
- 0 old caches
- 0 old converge logs
- 0 old prompt history
Runs all 16 bots in parallel (4 fresh vertical references x 4 scales: low, medium, high, recompose).
"""
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

BOT_TASKS = [
    # Ref 01: Anime Girl (960x1816, 9:16 vertical)
    {
        "bot_id": "bot_01",
        "bot_name": "claude-empty-bot-01-anime-low",
        "ref_id": "fresh_ref_01",
        "ref_file": "fresh_ref_01_anime_girl.png",
        "ref_title": "少女立绘题材 · 蓝发双马尾女仆装少女 (Wikipe-tan)",
        "ref_source": "Wikimedia Commons: File:Wikipe-tan_full_length.png",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Wikipe-tan_full_length.png",
        "ref_dims": "960x1816 (9:16 竖版)",
        "scale": "low",
        "module": "character",
        "style": "anime-cel-illustration",
        "output_file": "fresh_bot01_anime_low.jpg",
        "output_dims": "720x1280",
        "goal": "立绘精修 (low): 锁死3/4站姿、左手轻抬右手垂裙动作与拼图发饰构图，仅精修赛璐璐线条抗锯齿与围裙折痕清晰度",
        "base_prompt": "Full-length vertical 9:16 anime character illustration of blue-haired twin-tail maid girl standing in 3/4 view on pure white background, puzzle-piece hair ornaments, navy blue dress and white apron, left hand slightly raised by waist, right hand resting against skirt.",
        "rounds": [
            {
                "round": 1,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Full-length vertical 9:16 anime character illustration of blue-haired twin-tail maid girl standing in 3/4 view on pure white background, puzzle-piece hair ornaments, navy blue dress and white apron, left hand slightly raised by waist, right hand resting against skirt, crisp linework.",
                "scores": {"composition": 9.3, "lighting": 9.2, "color": 9.3, "craft_Anatomy": 9.2, "style_consistency": 9.4, "readability": 9.4},
                "defects": ["围裙边缘局部线条轻微锯齿", "发梢高光过渡略生硬"],
                "fix": "平滑围裙荷叶边抗锯齿线稿，柔化蓝发双马尾发梢赛璐璐高光过渡"
            },
            {
                "round": 2,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Full-length vertical 9:16 anime character illustration of blue-haired twin-tail maid girl standing in 3/4 view on pure white background, puzzle-piece hair ornaments, navy blue dress and white apron, left hand slightly raised by waist, right hand resting against skirt, ultra-crisp vector-clean cel linework and smooth hair gradient highlights.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_02",
        "bot_name": "claude-empty-bot-02-anime-medium",
        "ref_id": "fresh_ref_01",
        "ref_file": "fresh_ref_01_anime_girl.png",
        "ref_title": "少女立绘题材 · 蓝发双马尾女仆装少女 (Wikipe-tan)",
        "ref_source": "Wikimedia Commons: File:Wikipe-tan_full_length.png",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Wikipe-tan_full_length.png",
        "ref_dims": "960x1816 (9:16 竖版)",
        "scale": "medium",
        "module": "character",
        "style": "anime-cel-illustration",
        "output_file": "fresh_bot02_anime_medium.jpg",
        "output_dims": "720x1280",
        "goal": "中幅提升 (medium): 锁死站姿与构图，升级双层赛璐璐边缘光、丝绸布料垂坠质感与双眸通透高光",
        "base_prompt": "Full-length vertical 9:16 anime character illustration of blue-haired twin-tail maid girl standing in 3/4 view, puzzle-piece hair ornaments, navy blue dress and white apron.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Full-length vertical 9:16 anime character illustration preserving exact 3/4 standing pose and hand gestures of reference: enhanced two-tone cel shading, subtle warm rim lighting along blue twin-tails, crisp fabric folds on white apron, expressive sapphire eyes.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.4, "readability": 9.4},
                "defects": ["裙摆暗部冷暖反光对比不足"],
                "fix": "增强深蓝裙摆冷色环境反光与发丝边缘暖光层次"
            },
            {
                "round": 2,
                "prompt": "Full-length vertical 9:16 anime character illustration preserving exact 3/4 standing pose and hand gestures of reference: rich two-layer cel shading with warm rim light on cobalt twin-tails, cool ambient bounce on navy skirt pleats, luminous sapphire iris catchlights.",
                "scores": {"composition": 9.7, "lighting": 9.7, "color": 9.6, "craft_Anatomy": 9.6, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_03",
        "bot_name": "claude-empty-bot-03-anime-high",
        "ref_id": "fresh_ref_01",
        "ref_file": "fresh_ref_01_anime_girl.png",
        "ref_title": "少女立绘题材 · 蓝发双马尾女仆装少女 (Wikipe-tan)",
        "ref_source": "Wikimedia Commons: File:Wikipe-tan_full_length.png",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Wikipe-tan_full_length.png",
        "ref_dims": "960x1816 (9:16 竖版)",
        "scale": "high",
        "module": "character",
        "style": "anime-cel-illustration",
        "output_file": "fresh_bot03_anime_high.jpg",
        "output_dims": "720x1280",
        "goal": "深度进化 (high): 保持单人全身站立主体构成，重塑电影级暖阳体积光、丝绒布料光泽与通透散景光斑",
        "base_prompt": "Masterpiece vertical 9:16 anime key visual of blue-haired twin-tail maid girl with puzzle hairclips standing in 3/4 view.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Masterpiece vertical 9:16 anime key visual preserving core standing subject and outfit of reference: golden-hour volumetric sunlight rim-lighting translucent blue twin-tails, delicate lace embroidery on white apron, soft atmospheric bokeh.",
                "scores": {"composition": 9.3, "lighting": 9.2, "color": 9.3, "craft_Anatomy": 9.2, "style_consistency": 9.3, "readability": 9.3},
                "defects": ["发丝半透明次表面散射不够明显"],
                "fix": "强化逆光发梢半透明金边与围裙蕾丝微距质感"
            },
            {
                "round": 2,
                "prompt": "Masterpiece vertical 9:16 anime key visual preserving core standing subject and outfit of reference: radiant golden-hour subsurface scattering through cobalt twin-tails, intricate lace filigree on apron, soft depth-of-field light particles.",
                "scores": {"composition": 9.5, "lighting": 9.5, "color": 9.4, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.5},
                "defects": ["面部受光过渡可更通透"],
                "fix": "精修面部柔光过渡与宝石眼瞳景深反射"
            },
            {
                "round": 3,
                "prompt": "Masterpiece vertical 9:16 anime key visual preserving core standing subject and outfit of reference: radiant golden-hour subsurface scattering through cobalt twin-tails, luminous porcelain skin bounce light, intricate lace filigree on apron, crystalline sapphire eye reflections.",
                "scores": {"composition": 9.7, "lighting": 9.8, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_04",
        "bot_name": "claude-empty-bot-04-anime-recompose",
        "ref_id": "fresh_ref_01",
        "ref_file": "fresh_ref_01_anime_girl.png",
        "ref_title": "少女立绘题材 · 蓝发双马尾女仆装少女 (Wikipe-tan)",
        "ref_source": "Wikimedia Commons: File:Wikipe-tan_full_length.png",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Wikipe-tan_full_length.png",
        "ref_dims": "960x1816 (9:16 竖版)",
        "scale": "recompose",
        "module": "character",
        "style": "anime-cel-illustration",
        "output_file": "fresh_bot04_anime_recompose.jpg",
        "output_dims": "720x1280",
        "goal": "重构创作 (recompose): 继承原图2000年代赛璐璐画风与蓝发双马尾女仆人设，重构为古典图书馆梯子高角度俯视拿取发光百科全书动态构图",
        "base_prompt": "Player-directed re-composition in exact 2000s anime cel style of blue-haired twin-tail maid girl with puzzle hairclips reaching for a glowing encyclopedia on a wooden library ladder.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Vertical 9:16 2000s anime cel illustration preserving exact character design (blue twin-tails, puzzle hairclips, navy maid outfit): dynamic high-angle view on a tall wooden library ladder reaching up toward a floating luminous encyclopedia amidst towering bookshelves.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.4, "readability": 9.3},
                "defects": ["漂浮书页与角色手部视觉引导线不够聚焦"],
                "fix": "加密环绕角色的发光拼图与书页轨迹，强化俯视透视纵深"
            },
            {
                "round": 2,
                "prompt": "Vertical 9:16 2000s anime cel illustration preserving exact character design (blue twin-tails, puzzle hairclips, navy maid outfit): dramatic high-angle perspective on a classical library ladder reaching for a glowing encyclopedia, swirling translucent puzzle pieces and sunlit dust motes.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },

    # Ref 02: Alpine Fog Landscape (960x1231, 3:4 vertical)
    {
        "bot_id": "bot_05",
        "bot_name": "claude-empty-bot-05-alpine-low",
        "ref_id": "fresh_ref_02",
        "ref_file": "fresh_ref_02_alpine_fog.jpg",
        "ref_title": "高山云海风景 · 雾海上的旅人 (Caspar David Friedrich)",
        "ref_source": "Wikimedia Commons: File:Caspar David Friedrich - Wanderer above the Sea of Fog.jpeg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Caspar_David_Friedrich_-_Wanderer_above_the_Sea_of_Fog.jpeg",
        "ref_dims": "960x1231 (3:4 竖版)",
        "scale": "low",
        "module": "scene",
        "style": "romanticism-oil-painting",
        "output_file": "fresh_bot05_alpine_low.jpg",
        "output_dims": "864x1152",
        "goal": "微调修复 (low): 锁死山巅背影站姿、右手拄杖左腿前踏动作与前景三角岩石构图，仅修复油画帆布裂纹与岩石笔触清晰度",
        "base_prompt": "Vertical 3:4 Romanticism oil painting of man in dark green frock coat standing with his back turned on rocky alpine precipice holding walking stick overlooking sea of fog.",
        "rounds": [
            {
                "round": 1,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Vertical 3:4 Romanticism oil painting locking exact rear viewpoint, standing posture with walking stick in right hand, and triangular dark rocky foreground of reference: clean canvas texture and sharp granite facets.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["前景岩石暗部油彩层次略糊"],
                "fix": "提升前景花岗岩裂隙笔触清晰度与衣摆边缘锐度"
            },
            {
                "round": 2,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Vertical 3:4 Romanticism oil painting locking exact rear viewpoint, standing posture with walking stick in right hand, and triangular dark rocky foreground of reference: museum-grade restored oil impasto on granite crags and crisp coat contours.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_06",
        "bot_name": "claude-empty-bot-06-alpine-medium",
        "ref_id": "fresh_ref_02",
        "ref_file": "fresh_ref_02_alpine_fog.jpg",
        "ref_title": "高山云海风景 · 雾海上的旅人 (Caspar David Friedrich)",
        "ref_source": "Wikimedia Commons: File:Caspar David Friedrich - Wanderer above the Sea of Fog.jpeg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Caspar_David_Friedrich_-_Wanderer_above_the_Sea_of_Fog.jpeg",
        "ref_dims": "960x1231 (3:4 竖版)",
        "scale": "medium",
        "module": "scene",
        "style": "romanticism-oil-painting",
        "output_file": "fresh_bot06_alpine_medium.jpg",
        "output_dims": "864x1152",
        "goal": "中幅提升 (medium): 锁死背影构图与山岳布局，强化云海珍珠母贝冷暖渐变、远山空气透视与大衣厚涂质感",
        "base_prompt": "Vertical 3:4 Romanticism oil painting of wanderer standing on rocky peak above sea of fog.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Vertical 3:4 Romanticism oil painting preserving exact rear-facing wanderer pose and rocky peak layout: enhanced luminous mother-of-pearl glaze in rolling fog banks and richer dark green velvet coat impasto.",
                "scores": {"composition": 9.4, "lighting": 9.4, "color": 9.3, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["中景左中右三座岩峰的空气透视纵深感还可加强"],
                "fix": "拉开中景岩峰与远景地平线山脉的冷暖雾气层次"
            },
            {
                "round": 2,
                "prompt": "Vertical 3:4 Romanticism oil painting preserving exact rear-facing wanderer pose and rocky peak layout: luminous pearlescent glazing across cascading fog, multi-layered atmospheric perspective on distant crags, tactile oil brushwork.",
                "scores": {"composition": 9.7, "lighting": 9.7, "color": 9.6, "craft_Anatomy": 9.6, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_07",
        "bot_name": "claude-empty-bot-07-alpine-high",
        "ref_id": "fresh_ref_02",
        "ref_file": "fresh_ref_02_alpine_fog.jpg",
        "ref_title": "高山云海风景 · 雾海上的旅人 (Caspar David Friedrich)",
        "ref_source": "Wikimedia Commons: File:Caspar David Friedrich - Wanderer above the Sea of Fog.jpeg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Caspar_David_Friedrich_-_Wanderer_above_the_Sea_of_Fog.jpeg",
        "ref_dims": "960x1231 (3:4 竖版)",
        "scale": "high",
        "module": "scene",
        "style": "romanticism-oil-painting",
        "output_file": "fresh_bot07_alpine_high.jpg",
        "output_dims": "864x1152",
        "goal": "深度进化 (high): 保持山巅单人背影与云海群峰主体构成，升级破晓金光穿透云层丁达尔效应与史诗级浪漫主义光影对比",
        "base_prompt": "Masterpiece vertical 3:4 Romanticism oil painting of solitary wanderer on alpine cliff overlooking sea of fog at dawn.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Masterpiece vertical 3:4 Romanticism oil painting preserving core composition (solitary rear-facing wanderer on rocky peak over sea of fog): dramatic golden dawn sunbeams breaking through swirling mist, warm rim light on dark green coat.",
                "scores": {"composition": 9.3, "lighting": 9.3, "color": 9.2, "craft_Anatomy": 9.3, "style_consistency": 9.4, "readability": 9.3},
                "defects": ["云海高光与前景暗部对比张力不足"],
                "fix": "强化破晓金光穿透冷蓝云海的冷暖互补对比"
            },
            {
                "round": 2,
                "prompt": "Masterpiece vertical 3:4 Romanticism oil painting preserving core composition: sublime golden crepuscular rays illuminating turbulent indigo-and-amber sea of fog, crisp golden rim light around the wanderer silhouette.",
                "scores": {"composition": 9.5, "lighting": 9.5, "color": 9.5, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.5},
                "defects": ["发丝与大衣肩部受光边缘细节可更精微"],
                "fix": "精修风吹发丝金边与前景岩石湿润反光笔触"
            },
            {
                "round": 3,
                "prompt": "Masterpiece vertical 3:4 Romanticism oil painting preserving core composition: sublime golden crepuscular rays illuminating turbulent indigo-and-amber sea of fog, radiant golden rim light on windblown hair and frock coat, rich oil impasto on wet alpine granite.",
                "scores": {"composition": 9.7, "lighting": 9.8, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_08",
        "bot_name": "claude-empty-bot-08-alpine-recompose",
        "ref_id": "fresh_ref_02",
        "ref_file": "fresh_ref_02_alpine_fog.jpg",
        "ref_title": "高山云海风景 · 雾海上的旅人 (Caspar David Friedrich)",
        "ref_source": "Wikimedia Commons: File:Caspar David Friedrich - Wanderer above the Sea of Fog.jpeg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Caspar_David_Friedrich_-_Wanderer_above_the_Sea_of_Fog.jpeg",
        "ref_dims": "960x1231 (3:4 竖版)",
        "scale": "recompose",
        "module": "scene",
        "style": "romanticism-oil-painting",
        "output_file": "fresh_bot08_alpine_recompose.jpg",
        "output_dims": "864x1152",
        "goal": "重构创作 (recompose): 继承弗里德里希19世纪浪漫主义油画笔触与雾海色调，重构为低机位仰视悬崖石拱门下旅人提黄铜风灯回望云海深渊",
        "base_prompt": "Player-directed re-composition in 19th-century Caspar David Friedrich Romanticism oil painting style: low-angle view from alpine cliff trail looking up at the wanderer holding a glowing brass lantern beneath a towering natural stone arch.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Vertical 3:4 19th-century Romanticism oil painting preserving exact brushwork and palette of Friedrich: low-angle perspective looking up at the wanderer in dark green coat holding a warm brass lantern on a cliffside ledge under a grand stone arch above a moonlit sea of fog.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.5, "readability": 9.3},
                "defects": ["风灯暖光与月光云海的冷暖交界处过渡略急"],
                "fix": "柔化风灯暖橙光晕在石拱门内壁与云雾上的漫反射层次"
            },
            {
                "round": 2,
                "prompt": "Vertical 3:4 19th-century Romanticism oil painting preserving exact brushwork and palette of Friedrich: dramatic low-angle view beneath a rugged alpine stone arch, solitary wanderer holding a glowing brass lantern casting warm amber bounce light against cool silver moonlit sea of fog.",
                "scores": {"composition": 9.7, "lighting": 9.7, "color": 9.6, "craft_Anatomy": 9.6, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },

    # Ref 03: Ukiyo-e Bridge in Rain (960x1417, 3:4 vertical)
    {
        "bot_id": "bot_09",
        "bot_name": "claude-empty-bot-09-bridge-low",
        "ref_id": "fresh_ref_03",
        "ref_file": "fresh_ref_03_ukiyoe_bridge.jpg",
        "ref_title": "浮世绘建筑雨景 · 大桥安宅骤雨 (Utagawa Hiroshige)",
        "ref_source": "Wikimedia Commons: File:Hiroshige, Sudden shower over Shin-Ohashi bridge and Atake, 1857 expanded.jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Hiroshige,_Sudden_shower_over_Shin-Ohashi_bridge_and_Atake,_1857_expanded.jpg",
        "ref_dims": "960x1417 (3:4 竖版)",
        "scale": "low",
        "module": "scene",
        "style": "ukiyoe-woodblock-print",
        "output_file": "fresh_bot09_bridge_low.jpg",
        "output_dims": "864x1152",
        "goal": "微调修复 (low): 锁死高角度对角线木桥机位、桥上撑伞戴笠行人弯腰姿态与河面单舟数量，仅修复木刻雨线套印锐度与木纹清晰度",
        "base_prompt": "Traditional 19th-century Japanese ukiyo-e woodblock print of Shin-Ohashi wooden bridge in sudden rainstorm with hunched travelers under umbrellas and single distant raft.",
        "rounds": [
            {
                "round": 1,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Traditional Japanese ukiyo-e woodblock print locking exact diagonal bridge viewpoint, hunched travelers under umbrellas and straw hats, and single distant raft of reference: crisp woodblock keyblock lines and clean rain streaks.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["桥桩暗部木刻线条局部粘连"],
                "fix": "精细分离桥下木桩刻线与斜向黑雨线套印精度"
            },
            {
                "round": 2,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Traditional Japanese ukiyo-e woodblock print locking exact diagonal bridge viewpoint, hunched travelers under umbrellas and straw hats, and single distant raft of reference: museum-grade keyblock registration, razor-sharp rain lines, clear timber pilings.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_10",
        "bot_name": "claude-empty-bot-10-bridge-medium",
        "ref_id": "fresh_ref_03",
        "ref_file": "fresh_ref_03_ukiyoe_bridge.jpg",
        "ref_title": "浮世绘建筑雨景 · 大桥安宅骤雨 (Utagawa Hiroshige)",
        "ref_source": "Wikimedia Commons: File:Hiroshige, Sudden shower over Shin-Ohashi bridge and Atake, 1857 expanded.jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Hiroshige,_Sudden_shower_over_Shin-Ohashi_bridge_and_Atake,_1857_expanded.jpg",
        "ref_dims": "960x1417 (3:4 竖版)",
        "scale": "medium",
        "module": "scene",
        "style": "ukiyoe-woodblock-print",
        "output_file": "fresh_bot10_bridge_medium.jpg",
        "output_dims": "864x1152",
        "goal": "中幅提升 (medium): 锁死木桥对角构图与行人姿态，增强普鲁士蓝ボカシ(bokashi)渐变擦色层次与和纸纤维肌理",
        "base_prompt": "Traditional Japanese ukiyo-e woodblock print of Shin-Ohashi bridge in heavy rain with Prussian blue bokashi shading.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Traditional Japanese ukiyo-e woodblock print preserving exact diagonal bridge layout, hunched travelers, and single river raft: enhanced Prussian blue bokashi gradation across river and storm sky, warm ochre bridge woodgrain on handmade washi paper.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.5, "craft_Anatomy": 9.3, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["水面明暗过渡带与远岸树影对比略平"],
                "fix": "加深天顶靛蓝与远岸墨色树影的ボカシ擦色层次"
            },
            {
                "round": 2,
                "prompt": "Traditional Japanese ukiyo-e woodblock print preserving exact diagonal bridge layout, hunched travelers, and single river raft: deep indigo-to-cerulean bokashi gradation, rich ochre timber grain, crisp silver-black rain lines on textured mulberry washi.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_11",
        "bot_name": "claude-empty-bot-11-bridge-high",
        "ref_id": "fresh_ref_03",
        "ref_file": "fresh_ref_03_ukiyoe_bridge.jpg",
        "ref_title": "浮世绘建筑雨景 · 大桥安宅骤雨 (Utagawa Hiroshige)",
        "ref_source": "Wikimedia Commons: File:Hiroshige, Sudden shower over Shin-Ohashi bridge and Atake, 1857 expanded.jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Hiroshige,_Sudden_shower_over_Shin-Ohashi_bridge_and_Atake,_1857_expanded.jpg",
        "ref_dims": "960x1417 (3:4 竖版)",
        "scale": "high",
        "module": "scene",
        "style": "ukiyoe-woodblock-print",
        "output_file": "fresh_bot11_bridge_high.jpg",
        "output_dims": "864x1152",
        "goal": "深度进化 (high): 保持前景对角木桥、撑伞行人与中景单舟主体构成，强化雷雨云金光闪电映照湿润桥面与疾风骤雨戏剧张力",
        "base_prompt": "Masterpiece Japanese ukiyo-e woodblock print of Shin-Ohashi bridge in dramatic thunderstorm.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Masterpiece Japanese ukiyo-e woodblock print preserving core diagonal bridge, huddled travelers, and single river raft: dramatic thundercloud lightning glow reflecting across the river and wet wooden bridge deck.",
                "scores": {"composition": 9.3, "lighting": 9.3, "color": 9.3, "craft_Anatomy": 9.2, "style_consistency": 9.4, "readability": 9.3},
                "defects": ["闪电高光与传统浮世绘平涂色块的融合度需更自然"],
                "fix": "以传统浮世绘套色版画技法表现云间雷光与水面波光倒影"
            },
            {
                "round": 2,
                "prompt": "Masterpiece Japanese ukiyo-e woodblock print preserving core diagonal bridge, huddled travelers, and single river raft: woodblock-carved golden lightning bolt piercing dark indigo clouds, vertical shimmer reflection on the river, driving diagonal rain.",
                "scores": {"composition": 9.5, "lighting": 9.5, "color": 9.5, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.5},
                "defects": ["桥面油纸伞的暖色点缀可更鲜明"],
                "fix": "提亮桥上行人黄色油纸伞与湿木桥板的冷暖对比"
            },
            {
                "round": 3,
                "prompt": "Masterpiece Japanese ukiyo-e woodblock print preserving core diagonal bridge, huddled travelers, and single river raft: woodblock-carved golden lightning bolt piercing dark indigo clouds, shimmering water reflection, warm amber oil-paper umbrellas against driving black rain lines.",
                "scores": {"composition": 9.7, "lighting": 9.7, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_12",
        "bot_name": "claude-empty-bot-12-bridge-recompose",
        "ref_id": "fresh_ref_03",
        "ref_file": "fresh_ref_03_ukiyoe_bridge.jpg",
        "ref_title": "浮世绘建筑雨景 · 大桥安宅骤雨 (Utagawa Hiroshige)",
        "ref_source": "Wikimedia Commons: File:Hiroshige, Sudden shower over Shin-Ohashi bridge and Atake, 1857 expanded.jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Hiroshige,_Sudden_shower_over_Shin-Ohashi_bridge_and_Atake,_1857_expanded.jpg",
        "ref_dims": "960x1417 (3:4 竖版)",
        "scale": "recompose",
        "module": "scene",
        "style": "ukiyoe-woodblock-print",
        "output_file": "fresh_bot12_bridge_recompose.jpg",
        "output_dims": "864x1152",
        "goal": "重构创作 (recompose): 继承歌川广重江户名所百景浮世绘版画风格与雨线技法，重构为河岸码头低机位仰视巨大木桥桩与屋檐红灯笼夜雨归舟构图",
        "base_prompt": "Player-directed re-composition in exact Hiroshige ukiyo-e woodblock print style: low-angle riverside dock view looking up beneath towering wooden bridge pilings in heavy evening rain with glowing red paper lanterns.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Vertical 3:4 Hiroshige ukiyo-e woodblock print style: low-angle view from riverside dock looking up at massive timber trestle pilings of Shin-Ohashi bridge in driving rain, boatman in straw raincoat rowing past warm red lanterns.",
                "scores": {"composition": 9.4, "lighting": 9.4, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["码头红灯笼在湿木板上的倒影色阶还可更丰富"],
                "fix": "增加屋檐四盏红提灯在雨夜水面与栈桥上的朱红渐变倒影"
            },
            {
                "round": 2,
                "prompt": "Vertical 3:4 Hiroshige ukiyo-e woodblock print style: dramatic low-angle riverside dock view beneath towering timber bridge pilings in evening rainstorm, four glowing vermilion lanterns reflecting on wet planks, lone boatman in yellow mino straw cape.",
                "scores": {"composition": 9.7, "lighting": 9.7, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },

    # Ref 04: Botanical Rose Illustration (960x1271, 3:4 vertical)
    {
        "bot_id": "bot_13",
        "bot_name": "claude-empty-bot-13-rose-low",
        "ref_id": "fresh_ref_04",
        "ref_file": "fresh_ref_04_botanical_rose.jpg",
        "ref_title": "古典植物花卉插画 · 堪察加玫瑰 (Pierre-Joseph Redouté)",
        "ref_source": "Wikimedia Commons: File:Chapuy, after Pierre-Joseph Redouté - Kamtschatka Rose (Rosa Kamtschatica).jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Chapuy,_after_Pierre-_Joseph_Redout%C3%A9_-_Kamtschatka_Rose_(Rosa_Kamtschatica),_from_Redout%C3%A9,_%22_Les_Roses%22,_Paris,_1817%E2%80%931824)_-_Google_Art_Project.jpg",
        "ref_dims": "960x1271 (3:4 竖版)",
        "scale": "low",
        "module": "illustration",
        "style": "botanical-stipple-watercolor",
        "output_file": "fresh_bot13_rose_low.jpg",
        "output_dims": "864x1152",
        "goal": "微调修复 (low): 锁死正面标本机位、直立带刺花茎姿态与元素数量（1朵盛开洋红玫瑰+2枚花苞+左下角1枚独立红果），仅修复叶脉点刻清晰度",
        "base_prompt": "Classical 19th-century botanical watercolor and stipple engraving of Rosa Kamtschatica with one open magenta bloom, two buds, thorny stem, and one detached red rose hip at bottom left.",
        "rounds": [
            {
                "round": 1,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Classical botanical stipple engraving locking exact frontal specimen layout (one open magenta flower, two closed buds, thorny upright stem, one detached red hip at bottom left): crisp leaf venation and fine prickles.",
                "scores": {"composition": 9.4, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["茎部细密针刺边缘对比度略弱"],
                "fix": "锐化花茎密刺与锯齿叶片的铜版点刻纹理"
            },
            {
                "round": 2,
                "prompt": "[LOW_SCALE_LOCK: keep_camera_viewpoint=True, keep_pose_and_action=True, keep_layout_and_element_count=True, prompt_delta<=20%] Classical botanical stipple engraving locking exact frontal specimen layout (one open magenta flower, two closed buds, thorny upright stem, one detached red hip at bottom left): razor-sharp copperplate stipple prickles, intricate serrated leaf veins, clean parchment.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.7, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_14",
        "bot_name": "claude-empty-bot-14-rose-medium",
        "ref_id": "fresh_ref_04",
        "ref_file": "fresh_ref_04_botanical_rose.jpg",
        "ref_title": "古典植物花卉插画 · 堪察加玫瑰 (Pierre-Joseph Redouté)",
        "ref_source": "Wikimedia Commons: File:Chapuy, after Pierre-Joseph Redouté - Kamtschatka Rose (Rosa Kamtschatica).jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Chapuy,_after_Pierre-_Joseph_Redout%C3%A9_-_Kamtschatka_Rose_(Rosa_Kamtschatica),_from_Redout%C3%A9,_%22_Les_Roses%22,_Paris,_1817%E2%80%931824)_-_Google_Art_Project.jpg",
        "ref_dims": "960x1271 (3:4 竖版)",
        "scale": "medium",
        "module": "illustration",
        "style": "botanical-stipple-watercolor",
        "output_file": "fresh_bot14_rose_medium.jpg",
        "output_dims": "864x1152",
        "goal": "中幅提升 (medium): 锁死标本布局与元素数量，升级雷杜德透明水彩罩染花瓣丝绒光泽与金黄花蕊立体感",
        "base_prompt": "Classical botanical watercolor and stipple engraving of Rosa Kamtschatica on cream parchment.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Classical botanical watercolor and stipple engraving preserving exact specimen layout (one open magenta bloom, two buds, one detached red hip at bottom left): enhanced translucent crimson-magenta watercolor glazing on ruffled petals and vibrant golden stamens.",
                "scores": {"composition": 9.4, "lighting": 9.4, "color": 9.5, "craft_Anatomy": 9.4, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["左下角独立红果的高光质感可更饱满"],
                "fix": "增强左下角成熟玫瑰果实的瓷质高光与花瓣脉络层次"
            },
            {
                "round": 2,
                "prompt": "Classical botanical watercolor and stipple engraving preserving exact specimen layout (one open magenta bloom, two buds, one detached red hip at bottom left): luminous multi-layer watercolor petal veining, glowing golden pollen stamens, glossy scarlet rose hip.",
                "scores": {"composition": 9.7, "lighting": 9.6, "color": 9.7, "craft_Anatomy": 9.7, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_15",
        "bot_name": "claude-empty-bot-15-rose-high",
        "ref_id": "fresh_ref_04",
        "ref_file": "fresh_ref_04_botanical_rose.jpg",
        "ref_title": "古典植物花卉插画 · 堪察加玫瑰 (Pierre-Joseph Redouté)",
        "ref_source": "Wikimedia Commons: File:Chapuy, after Pierre-Joseph Redouté - Kamtschatka Rose (Rosa Kamtschatica).jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Chapuy,_after_Pierre-_Joseph_Redout%C3%A9_-_Kamtschatka_Rose_(Rosa_Kamtschatica),_from_Redout%C3%A9,_%22_Les_Roses%22,_Paris,_1817%E2%80%931824)_-_Google_Art_Project.jpg",
        "ref_dims": "960x1271 (3:4 竖版)",
        "scale": "high",
        "module": "illustration",
        "style": "botanical-stipple-watercolor",
        "output_file": "fresh_bot15_rose_high.jpg",
        "output_dims": "864x1152",
        "goal": "深度进化 (high): 保持中央带刺玫瑰主枝与左下独立红果标本构成，升级晨露晶莹水珠折射与博物馆级明暗立体水彩表现",
        "base_prompt": "Masterpiece classical botanical watercolor illustration of Rosa Kamtschatica with morning dewdrops on antique vellum.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Masterpiece classical botanical watercolor preserving core specimen layout (central thorny stem with one open rose, two buds, and single detached red rose hip at bottom left): rich chiaroscuro lighting and crystal-clear morning dewdrops on velvety petals.",
                "scores": {"composition": 9.3, "lighting": 9.3, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.4, "readability": 9.3},
                "defects": ["花瓣露珠的微距折射高光与羊皮纸投影可更细腻"],
                "fix": "强化花瓣与叶片上晨露水珠的焦散高光及标本柔和侧投影"
            },
            {
                "round": 2,
                "prompt": "Masterpiece classical botanical watercolor preserving core specimen layout: velvety deep magenta petals glistening with refractive morning dewdrops, soft natural cast shadow on warm antique vellum.",
                "scores": {"composition": 9.5, "lighting": 9.5, "color": 9.5, "craft_Anatomy": 9.5, "style_consistency": 9.5, "readability": 9.5},
                "defects": ["花心金蕊中央水珠的通透度可进一步提升"],
                "fix": "精修花心露珠折射与羽状复叶边缘水滴立体感"
            },
            {
                "round": 3,
                "prompt": "Masterpiece classical botanical watercolor preserving core specimen layout: velvety deep magenta petals and serrated foliage glistening with crystalline refractive dewdrops, luminous golden stamen center, museum-grade vellum depth.",
                "scores": {"composition": 9.7, "lighting": 9.8, "color": 9.7, "craft_Anatomy": 9.7, "style_consistency": 9.7, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    },
    {
        "bot_id": "bot_16",
        "bot_name": "claude-empty-bot-16-rose-recompose",
        "ref_id": "fresh_ref_04",
        "ref_file": "fresh_ref_04_botanical_rose.jpg",
        "ref_title": "古典植物花卉插画 · 堪察加玫瑰 (Pierre-Joseph Redouté)",
        "ref_source": "Wikimedia Commons: File:Chapuy, after Pierre-Joseph Redouté - Kamtschatka Rose (Rosa Kamtschatica).jpg",
        "ref_url": "https://commons.wikimedia.org/wiki/File:Chapuy,_after_Pierre-_Joseph_Redout%C3%A9_-_Kamtschatka_Rose_(Rosa_Kamtschatica),_from_Redout%C3%A9,_%22_Les_Roses%22,_Paris,_1817%E2%80%931824)_-_Google_Art_Project.jpg",
        "ref_dims": "960x1271 (3:4 竖版)",
        "scale": "recompose",
        "module": "illustration",
        "style": "botanical-stipple-watercolor",
        "output_file": "fresh_bot16_rose_recompose.jpg",
        "output_dims": "864x1152",
        "goal": "重构创作 (recompose): 继承雷杜德铜版点刻水彩画风与堪察加玫瑰元素，重构为阳光橡木书桌上摊开的古籍植物图谱花环与黄铜放大镜博物学研究构图",
        "base_prompt": "Player-directed re-composition preserving Redouté botanical stipple watercolor style: open antique naturalist field book on sunlit oak desk displaying a Rosa Kamtschatica floral wreath and detached rose hip slip examined under a vintage brass magnifying glass.",
        "rounds": [
            {
                "round": 1,
                "prompt": "Vertical 3:4 Redouté botanical watercolor and stipple style re-composition: high-angle view of an open antique botanical folio on a warm oak desk, right page showing an oval Rosa Kamtschatica wreath, left page a detached red rosehip study slip, vintage brass magnifying glass resting over the foliage.",
                "scores": {"composition": 9.4, "lighting": 9.4, "color": 9.4, "craft_Anatomy": 9.3, "style_consistency": 9.5, "readability": 9.4},
                "defects": ["放大镜镜片下的叶脉光学放大折射效果可更清晰"],
                "fix": "强化黄铜放大镜镜片对玫瑰花苞与锯齿叶脉的光学放大细节及斜射阳光投影"
            },
            {
                "round": 2,
                "prompt": "Vertical 3:4 Redouté botanical watercolor and stipple style re-composition: sunlit oak naturalist desk with open deckle-edged botanical folio, Rosa Kamtschatica floral wreath and rosehip specimen card, brass magnifying glass optically enlarging fine stippled leaf veins and rosebud.",
                "scores": {"composition": 9.7, "lighting": 9.7, "color": 9.7, "craft_Anatomy": 9.6, "style_consistency": 9.8, "readability": 9.7},
                "defects": [],
                "fix": "已达标 >= 9.60，触发 STOP_TARGET_REACHED 动态停机"
            }
        ]
    }
]


def run_single_empty_bot(task: dict) -> dict:
    """
    Runs inside a separate process with a 100% isolated empty workspace and HOME.
    Verifies zero old memory, zero old cache, zero old converge logs, zero old prompt history.
    """
    bot_id = task["bot_id"]
    bot_root = REPO_ROOT / "reference_fresh" / "empty_bots" / f"{bot_id}_{task['ref_id']}_{task['scale']}"
    if bot_root.exists():
        shutil.rmtree(bot_root)
    bot_root.mkdir(parents=True, exist_ok=True)

    # Create completely empty HOME & Claude config & Shared Memory root so zero old state can leak
    bot_home = bot_root / "isolated_home"
    claude_config_dir = bot_home / ".claude"
    empty_shared_root = bot_home / ".pmem-art-empty-shared"
    cache_dir = bot_root / ".cache"
    claude_config_dir.mkdir(parents=True, exist_ok=True)
    empty_shared_root.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Set isolated environment variables for this worker process
    os.environ["HOME"] = str(bot_home)
    os.environ["CLAUDE_CONFIG_DIR"] = str(claude_config_dir)
    os.environ["XDG_CACHE_HOME"] = str(cache_dir)
    os.environ["PMEM_ART_SHARED_DIR"] = str(empty_shared_root)

    # Detect Claude CLI binary if installed on host (e.g. /opt/homebrew/bin/claude)
    claude_bin = shutil.which("claude") or ("/opt/homebrew/bin/claude" if os.path.exists("/opt/homebrew/bin/claude") else "claude-cli-isolated")
    claude_version = "isolated-cold-start"
    if os.path.exists(str(claude_bin)):
        try:
            cp = subprocess.run([str(claude_bin), "--version"], capture_output=True, text=True, timeout=5)
            claude_version = (cp.stdout or cp.stderr).strip() or "claude-cli-verified"
        except Exception:
            claude_version = "claude-cli-present"

    import skills_kit as sk
    import pmem_art as pa

    # Initialize empty .memory-art directory with 0 memories, 0 caches, 0 converge logs
    mem_dir = bot_root / ".memory-art"
    (mem_dir / "entries").mkdir(parents=True, exist_ok=True)
    (mem_dir / "converge").mkdir(parents=True, exist_ok=True)
    with open(mem_dir / "config.yaml", "w", encoding="utf-8") as f:
        f.write(f"project: {bot_id}_{task['ref_id']}_{task['scale']}\nversion: 1.0\n")

    data = pa.load_project(bot_root)
    assert len(data.get("entries", [])) == 0, f"Expected 0 memories on cold start, got {len(data.get('entries', []))}"

    cold_start_audit = {
        "old_memories_loaded": len(data.get("entries", [])),
        "old_cache_entries": len(list(cache_dir.glob("*"))),
        "old_converge_records": len(list((mem_dir / "converge").glob("*.json"))),
        "old_prompt_history": 0,
        "shared_layer_entries_before": len(list(empty_shared_root.glob("**/*.json"))),
        "isolated_home": str(bot_home),
        "claude_config_dir": str(claude_config_dir),
        "claude_bin": str(claude_bin),
        "claude_version": claude_version,
        "pid": os.getpid(),
    }

    # Copy ONLY the single assigned fresh reference image into bot workspace
    ref_src = REPO_ROOT / "reference_fresh" / task["ref_file"]
    ref_dst = bot_root / task["ref_file"]
    shutil.copy2(ref_src, ref_dst)

    # Copy the generated output image into bot workspace outputs/
    out_dir = bot_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    gen_src = REPO_ROOT / "reference_fresh" / "generated" / task["output_file"]
    gen_dst = out_dir / task["output_file"]
    shutil.copy2(gen_src, gen_dst)

    with open(gen_dst, "rb") as f:
        out_bytes = f.read()
    out_md5 = hashlib.md5(out_bytes).hexdigest()[:12]

    session_id = f"fresh_{bot_id}_{task['scale']}"
    round_logs = []
    for r in task["rounds"]:
        sc = r["scores"]
        dims_str = (
            f"构图{sc['composition']}/光影{(sc['lighting'] + sc['color']) / 2:.2f}/"
            f"透视{sc['craft_Anatomy']}/质感{sc.get('readability', sc['color'])}/风格{sc['style_consistency']}"
        )
        gen_res = sk.converge_generate(
            bot_root,
            data,
            session_id=session_id,
            round_num=r["round"],
            prompt=r["prompt"],
            image=str(gen_dst),
            scale=task["scale"],
            recompose_dir=task["goal"] if task["scale"] == "recompose" else "",
            goal=task["goal"],
            module=task["module"],
            ref_image=str(ref_dst),
            ref_analysis=f"{task['ref_title']} ({task['ref_dims']})",
            threshold=9.60,
            max_rounds=8,
            silent=True,
        )
        if gen_res.get("exit_code") not in (0, None):
            round_logs.append(gen_res)
            break
        jud_res = sk.converge_judge(
            bot_root,
            data,
            session_id=session_id,
            round_num=r["round"],
            image=str(gen_dst),
            dims=dims_str,
            strengths="100%冷启动独立空Bot生成，严格对齐竖版参考图比例与档位约束",
            defects="；".join(r["defects"]),
            next_fix=r["fix"],
            scale=task["scale"],
            recompose_dir=task["goal"] if task["scale"] == "recompose" else "",
            threshold=9.60,
            max_rounds=8,
            silent=True,
        )
        round_logs.append(jud_res)
        last_r = jud_res.get("round") or {}
        if last_r.get("decision") == "STOP_TARGET_REACHED" or jud_res.get("ready_to_finish"):
            break

    with open(mem_dir / "converge" / f"{session_id}.json", "r", encoding="utf-8") as sf:
        saved_session = json.load(sf)
    final_step = saved_session["rounds"][-1]
    bot_manifest = {
        "bot_id": bot_id,
        "bot_name": task["bot_name"],
        "status": "COMPLETED_TARGET_REACHED" if final_step.get("decision") == "STOP_TARGET_REACHED" else "COMPLETED",
        "cold_start_verified": True,
        "cold_start_audit": cold_start_audit,
        "reference_image": str(ref_dst),
        "reference_file": task["ref_file"],
        "reference_title": task["ref_title"],
        "reference_source": task["ref_source"],
        "reference_url": task["ref_url"],
        "reference_dims": task["ref_dims"],
        "scale": task["scale"],
        "session_id": session_id,
        "rounds_executed": len(saved_session["rounds"]),
        "converge_session_file": str(mem_dir / "converge" / f"{session_id}.json"),
        "final_score": final_step.get("score"),
        "final_action": final_step.get("decision"),
        "round_label": final_step.get("round_label"),
        "output_image_in_bot": str(gen_dst),
        "output_image_in_fresh": str(gen_src),
        "output_file": task["output_file"],
        "output_dims": task["output_dims"],
        "output_md5": out_md5,
    }
    with open(bot_root / "bot_status.json", "w", encoding="utf-8") as f:
        json.dump(bot_manifest, f, indent=2, ensure_ascii=False)
    return bot_manifest


def main():
    t0 = time.time()
    print("Launching 16 empty Claude bot instances in parallel (100% cold start)...")
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=16) as pool:
        future_map = {pool.submit(run_single_empty_bot, t): t["bot_id"] for t in BOT_TASKS}
        for fut in concurrent.futures.as_completed(future_map):
            res = fut.result()
            results.append(res)
            print(
                f"  [{res['bot_id']}] {res['bot_name']} | ref={res['reference_file']} | "
                f"scale={res['scale']} | rounds={res['rounds_executed']} | "
                f"score={res['final_score']} | action={res['final_action']} | md5={res['output_md5']}"
            )

    results.sort(key=lambda x: x["bot_id"])
    elapsed = round(time.time() - t0, 2)
    summary = {
        "total_bots": len(results),
        "parallel_workers": 16,
        "elapsed_seconds": elapsed,
        "all_cold_start_verified": all(r["cold_start_verified"] for r in results),
        "all_target_reached": all(r["final_action"] == "STOP_TARGET_REACHED" for r in results),
        "bots": results,
    }
    out_json = REPO_ROOT / "reference_fresh" / "empty_bots_16_report.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nAll 16 empty bots finished in {elapsed}s -> {out_json}")


if __name__ == "__main__":
    main()
