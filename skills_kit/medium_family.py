"""Eleven media families plus a generic row. Four scales share one weight row.

Judge weights are fractions that sum to 1. Stop score is the weighted harmonic mean:

    1 / Σ (w_i / score_i)

which is the same as 100 / Σ (percent_i / score_i).
"""
from __future__ import annotations

from typing import Any

GENERAL_6D_KEYS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
    "flawlessness",
)

# Order is match priority. Q版、吉卜力、赛博朋克不单开一家。
_FAMILY_KEYS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pixel", ("像素画", "像素风", "像素图标", "点阵", "pixel art", "pixel-art", "8-bit", "8bit", "16-bit", "16bit", "像素")),
    ("emissive", ("霓虹", "魔法光", "全息", "灯牌", "自发光", "neon", "hologram")),
    ("photo", ("摄影", "胶片", "电影静帧", "照片", "photograph", "film still")),
    ("volume", ("三维", "黏土", "搪胶", "盲盒", "产品渲染", "c4d", "octane", "3d渲染")),
    ("collage", ("拼贴", "剪纸", "卡纸", "papercut", "paper-cut")),
    ("line", ("白描", "线描", "钢笔", "墨线", "十八描", "勾线")),
    ("cel", ("赛璐璐", "赛璐珞", "二分影", "硬边影", "cel-shad", "cel shading", "cel shad")),
    ("dry", ("粉彩", "油画棒", "彩铅", "炭笔", "素描", "速写", "pastel", "charcoal")),
    ("impasto", ("厚涂", "油画", "impasto")),
    ("wash", ("水彩", "水墨", "淡彩", "晕染", "watercolor", "ink wash")),
    ("flat", ("平涂", "扁平", "矢量", "海报", "浮世绘", "vector", "flat design")),
)

_FAMILY_WEIGHTS_PCT: dict[str, tuple[float, float, float, float, float, float]] = {
    # composition, lighting, perspective, texture, style, flawlessness
    "flat": (18.75, 11.25, 7.5, 18.75, 18.75, 25),
    "pixel": (18.75, 7.5, 11.25, 22.5, 15, 25),
    "cel": (15, 18.75, 15, 15, 11.25, 25),
    "dry": (11.25, 11.25, 15, 22.5, 15, 25),
    "line": (18.75, 7.5, 15, 22.5, 11.25, 25),
    "wash": (15, 11.25, 11.25, 22.5, 15, 25),
    "impasto": (15, 18.75, 11.25, 18.75, 11.25, 25),
    "photo": (15, 22.5, 11.25, 15, 11.25, 25),
    "volume": (15, 18.75, 11.25, 18.75, 11.25, 25),
    "collage": (18.75, 11.25, 11.25, 18.75, 15, 25),
    "emissive": (15, 26.25, 7.5, 11.25, 15, 25),
    "generic": (15, 15, 15, 15, 15, 25),
}

FAMILY_LABEL_ZH = {
    "flat": "平涂图形",
    "pixel": "像素",
    "cel": "赛璐璐",
    "dry": "干性媒介",
    "line": "线描排线",
    "wash": "水性晕染",
    "impasto": "厚涂",
    "photo": "摄影胶片",
    "volume": "立体渲染",
    "collage": "拼贴剪纸",
    "emissive": "自发光",
    "generic": "通用",
}

# scale → sentence. High for generic does not invent volume light.
_FAMILY_DIRECTIVE: dict[str, dict[str, str]] = {
    "flat": {
        "low": "修边线和色块溢出，不加光",
        "medium": "保画风与机位，加强色块边界和留白",
        "high": "抬边线、色块层次和构图，光仍平",
        "recompose": "按指定方向换机位，平涂和色块不动",
    },
    "pixel": {
        "low": "修断掉的像素和脏色，不抗锯齿",
        "medium": "保画风与机位，收紧色数，对齐像素格",
        "high": "抬剪影和像素节奏，禁止抹成平滑渐变",
        "recompose": "按指定方向换机位，像素格和色数不动",
    },
    "cel": {
        "low": "修线的断口和影形溢色，不把影晕开",
        "medium": "保画风与机位，整理硬边影的档数，保持平涂",
        "high": "抬线的干净程度和影形节奏，不加次表面散射",
        "recompose": "按指定方向换机位，线稿和硬边影不动",
    },
    "dry": {
        "low": "修纸纹脏点和糊掉的干笔触，不加重光",
        "medium": "保画风与机位，柔化光影和留白，保持干爽笔触",
        "high": "抬纸纹、飞白、留白和构图张力，光仍是软光、短接触影",
        "recompose": "按指定方向换机位，纸纹和软光不动",
    },
    "line": {
        "low": "修断线、糊线和多余墨点，不补色",
        "medium": "保画风与机位，整理疏密，不补明暗",
        "high": "抬线的疏密和轮廓，不铺水彩，不打棚拍光",
        "recompose": "按指定方向换机位，线的工具不动",
    },
    "wash": {
        "low": "修脏渍和糊成一团的积水，不改成厚涂",
        "medium": "保画风与机位，整理晕染层次和纸色",
        "high": "抬晕染层次和纸色，不做成棚拍高光",
        "recompose": "按指定方向换机位，晕染和纸色不动",
    },
    "impasto": {
        "low": "只修局部笔触和脏点，不大翻主光",
        "medium": "保画风与机位，柔化光影与次表面散射",
        "high": "抬体积光、冷暖、轮廓光与光影张力，可加风格内叙事",
        "recompose": "按指定方向换机位，笔触和色板不动，光可随新机位重铺",
    },
    "photo": {
        "low": "修脏点、过曝死白和假锐化，不改镜头",
        "medium": "保画风与机位，整理景深和颗粒，不加成绘画笔触",
        "high": "抬光比、空气和镜头层次，质感仍是颗粒",
        "recompose": "按指定方向换机位，镜头语言和颗粒不动",
    },
    "volume": {
        "low": "修穿模、糊边和假高光，不改材质种类",
        "medium": "保画风与机位，加强材质分界和接触影，保持软棚光",
        "high": "抬材质可读和形体，不画成厚涂，也不压成平面图标",
        "recompose": "按指定方向换机位，材质和光的类型不动",
    },
    "collage": {
        "low": "修层与层糊在一起的边，不涂平",
        "medium": "保画风与机位，整理每层的边和短投影",
        "high": "抬层次和剪影，不晕成一幅完整的画",
        "recompose": "按指定方向换机位，层的材料不动",
    },
    "emissive": {
        "low": "修光晕糊掉主体、核心过曝，不加外光",
        "medium": "保画风与机位，收束光晕，发光体本身仍可读",
        "high": "抬发光结构和色光层次，不另加一盏太阳",
        "recompose": "按指定方向换机位，发光方式不动",
    },
    "generic": {
        "low": "锁机位、姿态落点（手/脚触点跟参考像素，禁止搭膝改撑地）和笔触，只修看得见的脏点、断边，不发明新的光",
        "medium": "保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光",
        "high": "保媒介与身份，只抬已经看得见的层次",
        "recompose": "保画风色板，按指定方向重构机位，笔触和光的类型跟参考图",
    },
}

_FAMILY_HIGH_HINT = {
    "impasto": "最优方向：体积光/冷暖碰撞/轮廓光/叙事点缀",
    "generic": "最优方向：只抬参考里已经有的层次",
}


def family_weights(family: str) -> dict[str, float]:
    pct = _FAMILY_WEIGHTS_PCT.get(family) or _FAMILY_WEIGHTS_PCT["generic"]
    return {key: pct[i] / 100.0 for i, key in enumerate(GENERAL_6D_KEYS)}


def weighted_harmonic(
    scores: dict[str, float],
    weights: dict[str, float],
    keys: tuple[str, ...],
) -> float | None:
    """Weighted harmonic mean. Weights on `keys` are renormalized to 1."""
    if any(k not in scores for k in keys):
        return None
    wsum = sum(float(weights.get(k) or 0) for k in keys)
    if wsum <= 0:
        return None
    acc = 0.0
    for k in keys:
        x = float(scores[k])
        if x <= 0:
            return 0.0
        acc += (float(weights.get(k) or 0) / wsum) / x
    if acc <= 0:
        return None
    return round(1.0 / acc, 2)


def _keyword_hit(blob: str, key: str) -> bool:
    start = 0
    needle = key.lower()
    while True:
        idx = blob.find(needle, start)
        if idx < 0:
            return False
        # 「像素级 / 像素画质 / 像素画面」不是像素画。像素画 会误套在 像素画质 上。
        if blob.startswith("像素", idx):
            rest = blob[idx + len("像素") :]
            if rest.startswith(("级", "画质", "画面")):
                start = idx + len("像素")
                continue
        return True


def infer_medium_family(*parts: str) -> str:
    """Classify once from brief / module text. Unknown stays generic."""
    blob = " ".join(str(p or "") for p in parts).lower()
    if not blob.strip():
        return "generic"
    if "勾线平涂" in blob:
        return "cel"
    for name, keys in _FAMILY_KEYS:
        if any(_keyword_hit(blob, k) for k in keys):
            return name
    mod = blob
    if mod.startswith("ui.") or " ui." in f" {mod}" or mod.strip() in {"ui", "icon"}:
        return "flat"
    if "icon." in mod and "svg" in mod:
        return "line"
    return "generic"


def ensure_general_weights(weights: dict[str, float] | None) -> dict[str, float]:
    """Old 5-key scale weights gain 无瑕疵 at 25%; the other five keep their ratios inside 75%."""
    src = dict(weights or {})
    if "flawlessness" in src and abs(sum(float(src.get(k) or 0) for k in GENERAL_6D_KEYS) - 1.0) < 0.02:
        return {k: float(src.get(k) or 0) for k in GENERAL_6D_KEYS}
    craft = ("composition", "lighting_color", "perspective_anatomy", "texture_detail", "spec_style")
    base = {k: float(src.get(k) or 0) for k in craft}
    total = sum(base.values())
    if total <= 0:
        return family_weights("generic")
    out = {k: 0.75 * base[k] / total for k in craft}
    out["flawlessness"] = 0.25
    return out


def family_prompt_sentence(family: str, scale: str, recompose_dir: str = "") -> str:
    fam = family if family in _FAMILY_DIRECTIVE else "generic"
    s = scale if scale in ("low", "medium", "high", "recompose") else "medium"
    sentence = _FAMILY_DIRECTIVE[fam][s]
    if s == "recompose":
        target = (recompose_dir or "").strip() or "指定新机位"
        sentence = sentence.replace("指定方向", f"「{target}」")
        if "重构机位" not in sentence and fam == "generic":
            sentence = f"保画风色板，按「{target}」重构机位"
    return sentence


def family_best_hint(family: str, scale: str, *, recompose_bold: bool = False) -> str:
    if recompose_bold or scale in ("bold", "recompose_bold"):
        return "最优方向：画幅比+剪影一句，风格叙事大跳"
    if scale == "high":
        return _FAMILY_HIGH_HINT.get(family, "最优方向：只抬这一媒介已经有的长处")
    if scale == "recompose":
        return "最优方向：只写目标机位与布局"
    if scale == "low":
        return "最优方向：微质感（瓦当/纸齿/发丝），≤40字"
    return "最优方向：光影·空气·介质；可小幅姿态/局部布局"


def apply_family_to_profile(
    prof: dict[str, Any],
    *,
    family: str,
    recompose_dir: str = "",
    style_head: str = "",
    contract: str = "",
) -> dict[str, Any]:
    fam = family if family in _FAMILY_WEIGHTS_PCT else "generic"
    prof["medium_family"] = fam
    prof["dim_weights"] = family_weights(fam)
    scale = str(prof.get("scale") or "medium")
    sentence = family_prompt_sentence(fam, scale, recompose_dir)
    # low forbids pose change: keep limb-contact lock even after family sentence overwrite.
    if scale == "low" and prof.get("allow_action_pose_change") is False:
        if "姿态落点" not in sentence and "搭膝" not in sentence:
            sentence = f"{sentence.rstrip('。')}；锁姿态落点（手/脚触点跟参考像素，禁止搭膝改撑地）"
    head = (style_head or "").strip()
    prof["prompt_directive"] = f"{head}：{sentence}" if head else sentence
    prof["best_direction_hint"] = family_best_hint(fam, scale)
    if contract == "split":
        prof["contract"] = "split"
        prof["max_prompt_delta_ratio"] = 1.0
        prof["allow_viewpoint_change"] = True
        kept = []
        for item in list(prof.get("forbidden_changes") or []):
            text = str(item)
            low = text.lower()
            # 只拿掉机位锁。身份、姿态写在同一条里的红线留下。
            if any(k in text for k in ("身份", "姿态", "坐姿")) or "identity" in low:
                kept.append(item)
                continue
            if (
                "viewpoint_angle" in low
                or "不改机位" in text
                or "no_full_recompose" in low
                or "element_count" in low
                or "不增删主体" in text
            ):
                continue
            kept.append(item)
        prof["forbidden_changes"] = kept
        prof["prompt_directive"] = (
            f"{head}：身份图和结构图各管一件事，机位以结构图为准" if head
            else "身份图和结构图各管一件事，机位以结构图为准"
        )
        prof["next_fix_budget"] = "不使用四档的提示词预算，也不锁机位"
        prof["label"] = "多图分工 · 不走四档"
    return prof
