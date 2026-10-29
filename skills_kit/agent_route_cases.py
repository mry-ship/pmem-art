"""画师说法样本。标签是题目，路由器只能看句子和附图。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Case:
    text: str
    mode: str
    route_ids: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    reason: str = ""
    two_state: bool = False
    bucket: str = ""


def _add(out: list[Case], *, bucket: str, text: str, mode: str, routes: list[str] | None = None, images: list[str] | None = None, roles: list[str] | None = None, reason: str = "", two_state: bool = False) -> None:
    out.append(
        Case(
            text=text,
            mode=mode,
            route_ids=list(routes or []),
            images=list(images or []),
            roles=list(roles or []),
            reason=reason,
            two_state=two_state,
            bucket=bucket,
        )
    )


def build_cases() -> list[Case]:
    out: list[Case] = []
    subjects = ["窗边女孩", "青瓷杯", "驿站猫", "雨夜街道", "半身骑士", "旧船", "花瓶", "书店伙计", "雪地旅人", "灯塔", "厨师", "信使", "石桥", "麦田", "教室", "白猫"]
    styles = ["水彩", "厚涂", "平涂", "铅笔", "暖调", "冷调", "清晨", "雨天"]
    frames = ["半身", "全身", "头像", "街景", "静物", "侧脸"]
    verbs = ["画一张", "出一张", "来一张"]
    n = 0
    for subject in subjects:
        for style in styles:
            for frame in frames:
                verb = verbs[n % len(verbs)]
                n += 1
                if n > 360:
                    break
                _add(out, bucket="ordinary", text=f"{verb}{style}{frame}的{subject}", mode="default", routes=["draw.ordinary"])
            if n > 360:
                break
        if n > 360:
            break

    for i, subject in enumerate(subjects * 5):
        if i >= 80:
            break
        _add(
            out,
            bucket="ordinary_two_refs",
            text=f"两张附图都留着，画一张{subject}，没说哪张管什么",
            mode="default",
            routes=["draw.ordinary"],
            images=[f"ref/a{i}.png", f"ref/b{i}.png"],
        )

    people = ["女孩", "男孩", "老人", "店员"]
    for i, person in enumerate(people * 30):
        if i >= 120:
            break
        _add(
            out,
            bucket="ref_same_person",
            text=f"参考这张水彩，还是画这个{person}，不要换题材",
            mode="default",
            routes=["draw.ordinary"],
            images=["ref/style.png"],
        )

    news = ["修车的男孩", "一只猫", "一盏灯", "邮局", "渡船", "陶罐", "雪狐", "钟楼"]
    for i, new in enumerate(news * 20):
        if i >= 160:
            break
        _add(
            out,
            bucket="clone",
            text=f"参考这张的画风，别画原来的人，换成{new}",
            mode="skill",
            routes=["draw.clone"],
            images=["ref/style.png"],
        )

    moods = ["生气", "微笑", "闭眼", "侧目"]
    for i, mood in enumerate(moods * 35):
        if i >= 140:
            break
        _add(out, bucket="variant", text=f"同一个女孩，身份和机位不动，再来一张{mood}的表情", mode="skill", routes=["draw.variant"], images=["ref/girl.png"])

    for i in range(80):
        _add(out, bucket="not_variant", text=f"画这个角色的立绘，第{i}版，不要表情差分", mode="default", routes=["draw.ordinary"])

    for i in range(120):
        _add(
            out,
            bucket="multi",
            text="第一张是脸，第二张是坐姿，两张各管一件事",
            mode="skill",
            routes=["draw.multi"],
            images=[f"ref/face{i}.png", f"ref/pose{i}.png"],
            roles=["identity", "structure"],
        )

    for i in range(60):
        _add(
            out,
            bucket="multi_states",
            text="身份在第一张，结构在第二张，先画关上，再画打开",
            mode="skill",
            routes=["draw.multi", "draw.multi"],
            images=[f"id{i}.png", f"box{i}.png"],
            roles=["identity", "structure"],
            two_state=True,
        )

    for phrase in ("给我三套机位我自己挑", "来个镜头包，先别画", "远中近给我看看", "四套镜头给自己挑"):
        for i in range(20):
            _add(out, bucket="lens", text=f"{phrase}，角色是第{i}个旅人", mode="skill", routes=["draw.lens"])

    for i in range(60):
        _add(out, bucket="not_lens", text=f"镜头感强一点的半身，第{i}张，只要一张", mode="default", routes=["draw.ordinary"])

    for phrase in ("一整套主菜单，按钮要有按下和禁用", "HUD 整屏", "九宫格弹窗套件，带状态族", "做一整套界面"):
        for i in range(25):
            _add(out, bucket="ui", text=f"{phrase}，方案{i}", mode="skill", routes=["ui.kit"])

    for i in range(50):
        _add(out, bucket="single_popup", text=f"就一张空弹框，不要整套，第{i}张", mode="default", routes=["draw.ordinary"])

    for i in range(70):
        _add(out, bucket="icon_a", text=f"做一枚 1024 桌面图标，第{i}版", mode="skill", routes=["icon.a"])
        _add(out, bucket="icon_b", text=f"做一套线性 svg 图标，第{i}套", mode="skill", routes=["icon.b"])
        _add(out, bucket="icon_c", text=f"背包道具图标，256 透明底，第{i}个", mode="skill", routes=["icon.c"])

    for i in range(40):
        _add(out, bucket="icon_conflict", text=f"既要 1024 桌面图标，也要一套线性 svg，第{i}问", mode="stop", reason="icon_conflict")
        _add(out, bucket="icon_unspecified", text=f"画一个图标，别的没说，第{i}问", mode="stop", reason="icon_unspecified")

    for i in range(80):
        _add(out, bucket="merge", text=f"这把剑一档比一档大，做成合成梯，第{i}条", mode="skill", routes=["merge.ladder"])
        _add(out, bucket="key", text=f"一张概念海报，当主视觉，第{i}张", mode="skill", routes=["draw.key"])

    for i in range(50):
        _add(out, bucket="style", text=f"以后都按这张的颜色画，先锁风格，第{i}张", mode="skill", routes=["style.lock"], images=["ref/style.png"])
        _add(out, bucket="critique", text=f"只审这张，别画，第{i}张", mode="skill", routes=["critique.review"], images=["ref/in.png"])

    for i in range(40):
        _add(out, bucket="atlas", text=f"把散图归位，刷新图谱，第{i}批", mode="skill", routes=["atlas.file"])
        _add(out, bucket="coach", text=f"我想看看进步和短板，第{i}次", mode="skill", routes=["coach.report"])

    for i in range(50):
        _add(out, bucket="prompt", text=f"先写提示词，先不出图，第{i}套", mode="skill", routes=["prompt.write"])

    for i in range(30):
        _add(out, bucket="prompt_then_draw", text=f"先写提示词，然后再画一张立绘，第{i}套", mode="skill", routes=["prompt.write", "draw.ordinary"])
        _add(out, bucket="critique_then_draw", text=f"审完再改这张立绘，第{i}张", mode="skill", routes=["critique.review", "draw.ordinary"], images=["ref/in.png"])

    banned = ["局部修", "设定表", "分镜", "姿势锁", "同一场景换光", "画幅延展", "放大清稿", "序列帧", "平铺贴图", "带字主视觉", "字标", "色板点选", "情绪板"]
    for word in banned:
        for i in range(8):
            _add(out, bucket="unrecognized", text=f"帮我做{word}，第{i}件", mode="stop", reason="unrecognized")

    for i in range(30):
        _add(out, bucket="pixels", text=f"这两张参考的像素必须同时出现在同一张成图里，第{i}次", mode="stop", reason="simultaneous_pixels", images=["a.png", "b.png"])
        _add(out, bucket="hard", text=f"到底是整套界面还是一张插画，第{i}问", mode="stop", reason="hard_ambiguity")

    for i in range(40):
        _add(out, bucket="showcase", text=f"对比页把界面和桌面图标都重跑，第{i}页", mode="skill", routes=["ui.kit", "icon.a"])

    for i in range(20):
        _add(out, bucket="showcase_empty", text=f"做一页对比页，没写重跑哪几支，第{i}页", mode="stop", reason="showcase_unspecified")
        _add(out, bucket="named_unknown", text=f"/pmem-storyboard 画一张，第{i}次", mode="stop", reason="unrecognized")
        _add(out, bucket="named_draw", text=f"/pmem-draw 画一张窗边女孩，第{i}张", mode="default", routes=["draw.ordinary"])

    named = [
        ("/pmem-ui 做主菜单 HUD", "ui.kit"),
        ("/pmem-icon 1024 桌面图标", "icon.a"),
        ("/pmem-merge-ladder 做合成梯", "merge.ladder"),
        ("/pmem-style-lock 以后按这张", "style.lock"),
        ("/pmem-critique 只审", "critique.review"),
        ("/pmem-atlas 散图归位", "atlas.file"),
        ("/pmem-coach 看看进步", "coach.report"),
        ("/pmem-prompt 先写提示词，先不出图", "prompt.write"),
    ]
    for phrase, rid in named:
        for i in range(8):
            mode = "default" if rid == "draw.ordinary" else "skill"
            _add(out, bucket="named", text=f"{phrase}，第{i}次", mode=mode, routes=[rid], reason="named")

    for i in range(20):
        _add(out, bucket="negated_ban", text=f"不要做分镜，就画一张{subjects[i % len(subjects)]}", mode="default", routes=["draw.ordinary"])

    held = [
        ("帮我出个站在窗边的人", "default", ["draw.ordinary"], [], [], ""),
        ("水彩头像，看着舒服就行", "default", ["draw.ordinary"], [], [], ""),
        ("笔触照这张，主体改成雪狐", "skill", ["draw.clone"], [], [], ""),
        ("用附图的颜色，别画原来的人，画一艘船", "skill", ["draw.clone"], ["ref/a.png"], [], ""),
        ("同一张脸，换个画风", "skill", ["draw.variant"], ["ref/face.png"], [], ""),
        ("做一张四格表情表", "skill", ["draw.variant"], ["ref/face.png"], [], ""),
        ("附图一张管长相，一张管姿势", "skill", ["draw.multi"], ["a.png", "b.png"], ["identity", "structure"], ""),
        ("机位给三个方案我来选", "skill", ["draw.lens"], [], [], ""),
        ("主界面要一整屏，按钮分常态和按下", "skill", ["ui.kit"], [], [], ""),
        ("应用商店那种 1024 的启动图标", "skill", ["icon.a"], [], [], ""),
        ("从木剑长到圣剑，八个等级越来越大", "skill", ["merge.ladder"], [], [], ""),
        ("往后出图都用这张的色板", "skill", ["style.lock"], ["ref/style.png"], [], ""),
        ("先别动笔，帮我看看哪里不行", "skill", ["critique.review"], ["ref/in.png"], [], ""),
        ("仓库里那些没归类的图收进图谱", "skill", ["atlas.file"], [], [], ""),
        ("我最近画得怎么样，短板在哪", "skill", ["coach.report"], [], [], ""),
        ("把这句话扩成可以拿去画的说法，先别出图", "skill", ["prompt.write"], [], [], ""),
        ("只改手，别的地方别动", "stop", [], [], [], "unrecognized"),
        ("把这张往外延展画面", "stop", [], [], [], "unrecognized"),
        ("拉一条故事板", "stop", [], [], [], "unrecognized"),
        ("锁姿势，人别换动作", "stop", [], [], [], "unrecognized"),
        ("做一串逐帧", "stop", [], [], [], "unrecognized"),
        ("要一张无缝贴图", "stop", [], [], [], "unrecognized"),
        ("同一场景里只换光", "stop", [], [], [], "unrecognized"),
        ("放大后清一下线", "stop", [], [], [], "unrecognized"),
        ("出一张三视图设定", "stop", [], [], [], "unrecognized"),
        ("做一枚 1024 桌面图标，第64版", "skill", ["icon.a"], [], [], ""),
        ("做一套线性 svg 图标，第64套", "skill", ["icon.b"], [], [], ""),
    ]
    for text, mode, routes, images, roles, reason in held:
        _add(out, bucket="heldout", text=text, mode=mode, routes=routes, images=images, roles=roles, reason=reason)

    return out
