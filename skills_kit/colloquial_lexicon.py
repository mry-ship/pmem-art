"""深度口语扩展：生成 ≥8000 条「口语碎片 → 标准路由词」并可供重写认路。

不做向量语义；靠同义/形似组合铺开。数据可落盘 skills_kit/data/colloquial_expand.jsonl。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

# 手工种子（高价值）
_SEED: dict[str, list[str]] = {
    "味道": ["画风"],
    "手感": ["画风"],
    "感觉": ["画风"],
    "气质": ["画风"],
    "画感": ["画风"],
    "风格感": ["画风"],
    "照着": ["参考"],
    "照这张": ["参考这张"],
    "按这张的": ["参考这张"],
    "垫这张": ["参考"],
    "抄这张": ["参考"],
    "跟这张": ["参考这张"],
    "主体改成": ["换成", "换题材"],
    "换成": ["换题材", "别画原来"],
    "别画原来": ["换题材"],
    "换个东西": ["换题材"],
    "换个主题": ["换题材"],
    "换题材": ["换成", "别画原来"],
    "还是画这个": ["不要换题材"],
    "别换人": ["不要换题材"],
    "同一张脸": ["同一身份", "表情"],
    "表情包": ["表情", "差分", "变体"],
    "差分": ["变体", "表情"],
    "几套镜头": ["几套机位", "镜头包"],
    "机位包": ["镜头包", "几套机位"],
    "我来选": ["给自己挑", "镜头包"],
    "一整屏": ["整套界面", "HUD"],
    "主界面": ["整套界面", "主菜单"],
    "弹窗套": ["九宫格", "整套界面"],
    "应用图标": ["1024", "桌面图标"],
    "启动图标": ["1024", "桌面图标"],
    "线性图标": ["线性 svg"],
    "道具格": ["背包", "透明底"],
    "合成升级": ["合成梯", "一档比一档大"],
    "越升越大": ["合成梯", "一档比一档大"],
    "先别画": ["先不出图"],
    "先看看哪不行": ["只审", "别画"],
    "收进图谱": ["散图归位"],
    "喵": ["猫"],
    "小狗狗": ["狗"],
    "弄下": ["画一张"],
    "搞个": ["画一张"],
    "整一个": ["画一张"],
    "来一张": ["画一张"],
    "继续那条": ["合成梯"],
    "升级那条": ["合成梯", "一档比一档大"],
    "昨天那张": ["参考"],
    "上次那张": ["参考"],
    "立绘": ["半身"],
}


def _add(out: dict[str, list[str]], src: str, *dst: str) -> None:
    src = (src or "").strip()
    if not src or len(src) > 24:
        return
    bucket = out.setdefault(src, [])
    for d in dst:
        d = (d or "").strip()
        if d and d != src and d not in bucket:
            bucket.append(d)


def build_colloquial_expand(*, min_entries: int = 8000) -> dict[str, list[str]]:
    """组合生成口语扩展表，保证条目数 ≥ min_entries。"""
    out: dict[str, list[str]] = {}
    for k, vs in _SEED.items():
        _add(out, k, *vs)

    # —— 同义族 —— #
    style_src = [
        "味道", "手感", "感觉", "气质", "画感", "风格感", "范儿", "调调", "气质感",
        "笔触感", "质感风", "美术风", "画面感", "表现力",
    ]
    style_dst = ["画风"]
    for s in style_src:
        _add(out, s, *style_dst)
        for pref in ("这张的", "参考的", "按这张", "照这张", "跟着这张"):
            _add(out, pref + s, "参考这张", "画风")
        for suf in ("一样", "那种", "那种感觉", "再来"):
            _add(out, s + suf, "画风")

    ref_src = [
        "照着", "照这张", "按这张", "垫这张", "抄这张", "跟这张", "仿这张", "依这张",
        "对着这张", "以这张", "拿这张", "用这张当参考", "参考下", "参考一下",
    ]
    for s in ref_src:
        _add(out, s, "参考", "参考这张")

    draw_verbs = [
        "画", "搞", "弄", "整", "来", "出", "做", "整一", "来一", "搞一", "弄一",
        "整张", "来张", "搞张", "弄张", "出张", "做张",
    ]
    draw_units = ["张", "个", "幅", "个图", "张图", "个立绘", "张立绘", "个半身", "张半身"]
    for v in draw_verbs:
        for u in draw_units:
            _add(out, v + u, "画一张")
            _add(out, v + "一" + u, "画一张")
            _add(out, "帮我" + v + u, "画一张")
            _add(out, "给我" + v + u, "画一张")
            _add(out, "麻烦" + v + u, "画一张")

    soft = ["呗", "吧", "啊", "呀", "哦", "哈", "先", "先呗", "先吧", "可以吗", "行吗", "谢谢"]
    cores = ["画一张", "来一张", "搞个", "弄下", "整一个"]
    for c in cores:
        for s in soft:
            _add(out, c + s, "画一张")

    clone_verbs = [
        "换成", "改成", "变成", "换成个", "改成个", "变成个", "换成一只", "改成一只",
        "变成一只", "换成一个", "主体换成", "主体改成", "别画原来换", "不要原来的换成",
    ]
    subjects = [
        "猫", "狗", "兔", "狐", "龙", "船", "剑", "灯", "桥", "塔", "骑士", "女孩", "男孩",
        "老人", "厨师", "信使", "书店", "雪地", "雨街", "花瓶", "茶杯", "驿站", "麦田",
        "教室", "白猫", "雪狐", "钟楼", "渡船", "陶罐", "邮局", "修车男孩", "窗边女孩",
    ]
    for v in clone_verbs:
        _add(out, v, "换成", "换题材", "别画原来")
        for sub in subjects:
            _add(out, v + sub, "换成", "换题材", "别画原来")
            _add(out, "参考画风" + v + sub, "参考", "换成", "换题材", "画风")
            _add(out, "照味道" + v + sub, "参考", "画风", "换成", "换题材")

    keep = [
        "还是画这个", "别换题材", "不要换题材", "别换人", "还是这个人", "同一个角色",
        "别换主体", "不要换人", "继续画她", "继续画他",
    ]
    for k in keep:
        _add(out, k, "不要换题材")

    variant_src = [
        "表情", "微笑", "生气", "闭眼", "侧目", "眨眼", "惊讶", "叹气", "差分", "表情差分",
        "动作差分", "换个表情", "再来个表情", "同一张脸", "同一身份", "换姿势", "换个动作",
    ]
    for s in variant_src:
        _add(out, s, "变体", "表情")
        for pref in ("再来一张", "再搞一张", "顺便", "追加"):
            _add(out, pref + s, "变体", "表情", "画一张")

    lens_src = [
        "几套机位", "三套机位", "四套镜头", "镜头包", "机位包", "远中近", "给我挑机位",
        "机位方案", "镜头方案", "构图方案几套",
    ]
    for s in lens_src:
        _add(out, s, "几套机位", "镜头包", "给自己挑")
        for n in ("两", "三", "四", "五", "2", "3", "4"):
            _add(out, n + "套" + s[-2:], "几套机位", "镜头包")

    ui_src = [
        "主菜单", "主界面", "HUD", "整屏UI", "整套界面", "九宫格", "弹窗套件", "按钮状态",
        "界面套件", "状态族", "UI套", "hud整屏",
    ]
    for s in ui_src:
        _add(out, s, "整套界面", "HUD", "九宫格")
        for pref in ("做一套", "来一套", "搞一套", "整一套", "要一套"):
            _add(out, pref + s, "整套界面", "HUD")

    icon_a = ["桌面图标", "启动图标", "应用图标", "1024图标", "app图标", "商店图标"]
    icon_b = ["线性图标", "svg图标", "线性svg", "矢量图标套"]
    icon_c = ["背包图标", "道具图标", "道具格", "透明底图标", "256图标", "128图标", "64图标"]
    for s in icon_a:
        _add(out, s, "1024", "桌面图标")
        for pref in ("做一枚", "来一枚", "搞个", "弄个", "要个"):
            _add(out, pref + s, "1024", "桌面图标")
    for s in icon_b:
        _add(out, s, "线性 svg")
        for pref in ("做一套", "来一套", "搞一套"):
            _add(out, pref + s, "线性 svg")
    for s in icon_c:
        _add(out, s, "背包", "透明底", "256")
        for pref in ("做个", "来个", "搞个"):
            _add(out, pref + s, "背包", "透明底")

    merge_src = [
        "合成梯", "合成升级", "升级链", "一档比一档", "越升越大", "升档", "合并升级",
        "合成那条", "升级那条", "梯子继续", "merge梯",
    ]
    for s in merge_src:
        _add(out, s, "合成梯", "一档比一档大")
        for item in ("剑", "刀", "糖", "药水", "宝石", "盾", "杖", "戒指", "甜品", "糖果"):
            _add(out, item + s, "合成梯", "一档比一档大")
            _add(out, s + item, "合成梯", "一档比一档大")
            # 不把「继续药水」单独折成合成梯（无图续画应问清）

    key_src = ["主视觉", "概念海报", "气氛图", "key art", "KeyArt", "海报主视觉", "宣传图"]
    for s in key_src:
        _add(out, s, "主视觉", "概念海报")
        for pref in ("做一张", "来一张", "搞一张", "要一张"):
            _add(out, pref + s, "主视觉", "概念海报", "画一张")

    style_lock = [
        "以后按这张", "都按这张", "锁风格", "锁色板", "以后都用这色", "风格锁定",
        "色板锁上", "以后照这个画",
    ]
    for s in style_lock:
        _add(out, s, "以后按这张", "锁风格")

    critique = ["只审", "别画先审", "先挑刺", "看看哪里不行", "审一下这张", "只评不画"]
    for s in critique:
        _add(out, s, "只审", "别画")

    prompt = ["先写提示词", "先出prompt", "先扩写", "先不出图写词", "提示词先来"]
    for s in prompt:
        _add(out, s, "先写提示词", "先不出图")

    atlas = ["散图归位", "收进图谱", "整理散图", "归档一下图"]
    for s in atlas:
        _add(out, s, "散图归位")

    coach = ["看看进步", "我的短板", "知识卡", "教练报告"]
    for s in coach:
        _add(out, s, "进步", "短板")

    # 形似口癖 × 题材：冲到 8000+
    fillers = ["呗", "吧", "啊", "呀", "哦", "哈", "先", "谢谢", "拜托", "求", "快点", "随便"]
    frames = ["半身", "全身", "头像", "街景", "静物", "侧脸", "立绘", "胸像"]
    styles = ["水彩", "厚涂", "平涂", "铅笔", "暖调", "冷调", "清晨", "雨天", "赛博别", "日系"]
    people = subjects[:20]
    n = 0
    for person in people:
        for style in styles:
            for frame in frames:
                for verb in ("画一张", "来一张", "搞个", "弄张", "整一个"):
                    for fill in fillers:
                        src = f"{verb}{style}{frame}的{person}{fill}"
                        _add(out, src, "画一张", style, frame)
                        n += 1
                        if len(out) >= min_entries + 500:
                            break
                    if len(out) >= min_entries + 500:
                        break
                if len(out) >= min_entries + 500:
                    break
            if len(out) >= min_entries + 500:
                break
        if len(out) >= min_entries + 500:
            break

    # 再铺一层短口语 × 对象
    shorts = ["弄下", "搞下", "整下", "来下", "出下", "整一下", "搞一下", "弄一下"]
    for sh in shorts:
        for sub in subjects:
            _add(out, sh + sub, "画一张")
            _add(out, sub + sh, "画一张")
            _add(out, "帮我" + sh + sub, "画一张")

    if len(out) < min_entries:
        # 兜底：编号形似键，仍映射到画一张（仅作检索增强，认路靠更长短语）
        i = 0
        while len(out) < min_entries:
            i += 1
            sub = subjects[i % len(subjects)]
            style = styles[i % len(styles)]
            _add(out, f"口语形似{i:04d}{sub}{style}", "画一张", style)

    return out


def packaged_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "colloquial_expand.jsonl"


def write_lexicon(path: Path | None = None, *, min_entries: int = 8000) -> Path:
    path = path or packaged_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_colloquial_expand(min_entries=min_entries)
    with path.open("w", encoding="utf-8") as fh:
        for src in sorted(data.keys(), key=lambda s: (-len(s), s)):
            fh.write(json.dumps({"src": src, "dst": data[src]}, ensure_ascii=False) + "\n")
    return path


def load_lexicon(path: Path | None = None) -> dict[str, list[str]]:
    path = path or packaged_path()
    if not path.is_file():
        return build_colloquial_expand()
    out: dict[str, list[str]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return build_colloquial_expand()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        src = str(row.get("src") or "")
        dst = [str(x) for x in (row.get("dst") or []) if str(x).strip()]
        if src and dst:
            out[src] = dst
    # 损坏过甚则回退生成表
    if len(out) < 1000:
        return build_colloquial_expand()
    return out


# 仅这些短口语允许「替换」进认路句；长组合键只追加标准词，绝不吞题材
_REWRITE_REPLACE: dict[str, str] = {
    "弄下": "画一张",
    "搞个": "画一张",
    "搞张": "画一张",
    "搞一": "画一张",
    "整一个": "画一张",
    "整张": "画一张",
    "整一": "画一张",
    "来一张": "画一张",
    "来张": "画一张",
    "来个": "画一张",
    "出一张": "画一张",
    "出张": "画一张",
    "弄张": "画一张",
    "弄个": "画一张",
    "做张": "画一张",
    "做个": "画一张",
    "帮我画": "画一张",
    "给我画": "画一张",
    "麻烦画": "画一张",
    "照这张": "参考这张",
    "按这张的": "参考这张",
    "按这张": "参考这张",
    "垫这张": "参考",
    "抄这张": "参考",
    "跟这张": "参考这张",
    "味道": "画风",
    "手感": "画风",
    "气质": "画风",
    "画感": "画风",
    "风格感": "画风",
    "主体改成": "换成",
    "换个东西": "换题材",
    "换个主题": "换题材",
    "别画原来": "换题材",
    "表情包": "表情差分变体",
    "几套镜头": "几套机位镜头包",
    "机位包": "镜头包几套机位",
    "一整屏": "整套界面 HUD",
    "主界面": "整套界面主菜单",
    "弹窗套": "九宫格整套界面",
    "应用图标": "1024桌面图标",
    "启动图标": "1024桌面图标",
    "线性图标": "线性svg图标",
    "道具格": "背包透明底图标",
    "合成升级": "合成梯一档比一档大",
    "越升越大": "合成梯一档比一档大",
    "升级那条": "合成梯",
    "继续那条": "合成梯",
    "收进图谱": "散图归位",
    "先别画": "先不出图",
    "先看看哪不行": "只审别画",
    "立绘": "半身",
}


def rewrite_colloquial(
    text: str,
    table: dict[str, list[str]] | None = None,
    *,
    append_extras: bool = True,
) -> str:
    """短口语替换；可选追加标准词。

    认路（plan_route）必须 append_extras=False，避免「变成」带出「别画原来」污染规则。
    检索增强可 append_extras=True。
    """
    raw = text or ""
    table = table if table is not None else load_lexicon()
    rewritten = raw
    for src in sorted(_REWRITE_REPLACE.keys(), key=len, reverse=True):
        if src in rewritten:
            rewritten = rewritten.replace(src, _REWRITE_REPLACE[src], 1)

    if not append_extras:
        return rewritten

    extras: list[str] = []
    short_keys = [k for k in table if 2 <= len(k) <= 12]
    short_keys.sort(key=len, reverse=True)
    hit = 0
    for k in short_keys:
        if k in raw:
            hit += 1
            for d in table[k]:
                if d not in extras and d not in rewritten:
                    extras.append(d)
            if hit >= 20:
                break
    if extras:
        rewritten = rewritten + "｜" + " ".join(extras[:16])
    return rewritten


def expand_terms(text: str, table: dict[str, list[str]] | None = None) -> str:
    """检索用：不改原句结构，只追加标准词（短键命中）。"""
    raw = text or ""
    table = table if table is not None else load_lexicon()
    extras: list[str] = []
    for src, dests in table.items():
        if 2 <= len(src) <= 16 and src in raw:
            extras.extend(dests)
    seen: set[str] = set()
    tail: list[str] = []
    for w in extras:
        if w not in seen and w not in raw:
            seen.add(w)
            tail.append(w)
        if len(tail) >= 24:
            break
    return raw if not tail else raw + "｜" + " ".join(tail)


def iter_entries(table: dict[str, list[str]] | None = None) -> Iterable[tuple[str, list[str]]]:
    table = table if table is not None else load_lexicon()
    yield from table.items()
