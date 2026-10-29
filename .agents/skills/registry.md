# 技能注册表

来源：`skills_kit/skill_specs.py`。生成：`python3 pmem_art.py skills --install`。

## tighten

1. 没人要「几套镜头」→ 不进镜头包。有参考图本身不是镜头包。
2. 有参考，但没说新题材、新物件、新角色 → 普通图，不进克隆。
3. 单张弹框、只要一张图标 → 不升成整套界面或图标集。整套才去界面 / 图标。有参考又要换题材的这一张，走克隆。
4. 只说「画这个角色」→ 普通图或原画，不进变体。变体要出现换画风、表情或动作。
5. 两张图分工不同，或关/开这类状态和身份不在同一张图上 → 多图分工。一张图改表情仍走变体。
6. 回显的类型必须和实际执行的合同是同一个。玩家下一句改口，丢掉这一支重来；已经画完的图不能拿去冒充新合同的结果。

## 路由

按 phase 从小到大对，停在第一条对上的行。普通图 phase 最大，只作兜底，不要把它的「以上都不是」当成关键词命中。

| id | phase | when | skill | heading | routable |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ui.kit` | 10 | 玩家要整屏、HUD、弹窗套件、九宫格、按钮状态 | `pmem-ui` | # `/pmem-ui` — SpriteCook 式 UI Kit / HUD / 九宫格整套生成 | true |
| `icon.a` | 20 | 桌面图标、1024 母版 | `pmem-icon` | ## 二之二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标） | true |
| `icon.b` | 21 | 一套线性 SVG | `pmem-icon` | ## 二、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge） | true |
| `icon.c` | 22 | 背包道具格 | `pmem-icon` | ### 二之三、Mode C：游戏道具透明底栅格图标（64/128/256px PNG，非 SVG） | true |
| `merge.ladder` | 30 | 同一套东西一档比一档更大，L1–L8 | `pmem-merge-ladder` | # `/pmem-merge-ladder` — 同域合成梯 | true |
| `draw.lens` | 40 | 玩家明确要几套机位 / 镜头 / 光给自己挑 | `pmem-draw` | ## 合同 · 镜头包 | true |
| `draw.clone` | 50 | 有参考，并且要换一个新题材，锁的是画风 | `pmem-draw` | ## 合同 · 克隆 | true |
| `draw.variant` | 60 | 已有角色要换画风，或做表情 / 动作差分。身份和机位已经在同一张图上 | `pmem-draw` | ## 合同 · 变体 | true |
| `draw.multi` | 70 | 两张及以上的图各管一件事，或同一物件的多个状态要锁同一个机位，机位和身份不在同一张图上 | `pmem-draw` | ## 合同 · 多图分工 | true |
| `draw.key` | 80 | 主视觉、Key Art、气氛图、概念海报 | `pmem-draw` | ## 合同 · 原画 | true |
| `style.lock` | 90 | 以后按这张画 | `pmem-style-lock` | # `/pmem-style-lock` — 样张提炼风格圣经与色板锁定 | true |
| `critique.review` | 91 | 只审、不画 | `pmem-critique` | # `/pmem-critique` — 主美级六维审稿与红线入库 | true |
| `atlas.file` | 92 | 散图归位 | `pmem-atlas` | # `/pmem-atlas` — 整理散图与刷新可视化图谱 | true |
| `coach.report` | 93 | 要看进步、短板、知识卡 | `pmem-coach` | # `/pmem-coach` — 进步 / 短板 / 知识（三条偷看合成一条） | true |
| `prompt.write` | 94 | 要写提示词、扩写 brief | `pmem-prompt` | # `/pmem-prompt` — 提示词生成器（按类型分流） | true |
| `draw.ordinary` | 100 | 以上都不是 | `pmem-draw` | ## 二、标准执行流程（Step 1 ~ Step 3） | true |

## unroutable_headings

（无）
