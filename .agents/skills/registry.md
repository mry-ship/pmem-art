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

执行以 `python3 pmem_art.py route` 的 `route_ids` 为准。这张表核对 heading；**交给执行侧用 `pack_headings` + `slice_route_body`**（出图合同=零点五+第二节+合同；图标=Mode+§五清单+记忆静默）。phase 是查阅顺序，不要用它改判。普通图 phase 最大，只作兜底。

| id | phase | when | skill | heading | pack | routable |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ui.kit` | 10 | 玩家要整屏、HUD、弹窗套件、九宫格、按钮状态 | `pmem-ui` | # `/pmem-ui` — SpriteCook 式 UI Kit / HUD / 九宫格整套生成 | ## 执行卡 · UI（Agent 必读） | true |
| `icon.a` | 20 | 桌面图标、1024 母版 | `pmem-icon` | ## 二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标） | ## 二、Mode A：App Icon 1… + ### Mode A + ## 记忆静默 / 履历可见（Agent 必… | true |
| `icon.b` | 21 | 一套线性 SVG | `pmem-icon` | ## 三、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge） | ## 三、Mode B：一致化 SVG 矢量… + ### Mode B + ## 记忆静默 / 履历可见（Agent 必… | true |
| `icon.c` | 22 | 背包道具格 | `pmem-icon` | ## 四、Mode C：游戏道具隔离底栅格图标（64/128/256px PNG，非 SVG） | ## 四、Mode C：游戏道具隔离底栅格图… + ### Mode C + ## 记忆静默 / 履历可见（Agent 必… | true |
| `merge.ladder` | 30 | 同域升级梯（默认整表一组、L1–L8；有参考跟格数，点名数量跟点名；仅点名逐格才 per_cell）；糖果/甜品默认 shop_ladder；工具瓶罐可 same_object；未点名非糖果可轻门 | `pmem-merge-ladder` | # `/pmem-merge-ladder` — 同域合成梯 | ## 执行卡 · 合成梯（Agent 必读；… + ## 禁止 | true |
| `draw.lens` | 40 | 玩家明确要几套机位 / 镜头 / 光给自己挑 | `pmem-draw` | ## 合同 · 镜头包 | ## 零点五、开画前强制 route（与总控… + ## 合同 · 镜头包 | true |
| `draw.clone` | 50 | 有参考，并且要换一个新题材，锁的是画风 | `pmem-draw` | ## 合同 · 克隆 | ## 零点五、开画前强制 route（与总控… + ## 执行卡 · 出图闭环（Agent 必读… + ## 合同 · 克隆 + ## 记忆静默 / 履历可见（Agent 必… | true |
| `draw.variant` | 60 | 已有角色要换画风，或做表情 / 动作差分。身份和机位已经在同一张图上 | `pmem-draw` | ## 合同 · 变体 | ## 零点五、开画前强制 route（与总控… + ## 执行卡 · 出图闭环（Agent 必读… + ## 合同 · 变体 + ## 记忆静默 / 履历可见（Agent 必… | true |
| `draw.multi` | 70 | 两张及以上的图各管一件事，或同一物件的多个状态要锁同一个机位，机位和身份不在同一张图上 | `pmem-draw` | ## 合同 · 多图分工 | ## 零点五、开画前强制 route（与总控… + ## 执行卡 · 出图闭环（Agent 必读… + ## 合同 · 多图分工 + ## 记忆静默 / 履历可见（Agent 必… | true |
| `draw.key` | 80 | 主视觉、Key Art、气氛图、概念海报 | `pmem-draw` | ## 合同 · 原画 | ## 零点五、开画前强制 route（与总控… + ## 执行卡 · 出图闭环（Agent 必读… + ## 合同 · 原画 + ## 记忆静默 / 履历可见（Agent 必… | true |
| `style.lock` | 90 | 以后按这张画 | `pmem-style-lock` | # `/pmem-style-lock` — 样张提炼风格圣经与色板锁定 | # `/pmem-style-lock` —… | true |
| `critique.review` | 91 | 只审、不画 | `pmem-critique` | # `/pmem-critique` — 主美级六维审稿与红线入库 | # `/pmem-critique` — 主… | true |
| `atlas.file` | 92 | 散图归位 | `pmem-atlas` | # `/pmem-atlas` — 整理散图与刷新可视化图谱 | # `/pmem-atlas` — 整理散图… | true |
| `coach.report` | 93 | 要看进步、短板、知识卡 | `pmem-coach` | # `/pmem-coach` — 进步 / 短板 / 知识（三条偷看合成一条） | # `/pmem-coach` — 进步 /… | true |
| `prompt.write` | 94 | 要写提示词、扩写 brief | `pmem-prompt` | # `/pmem-prompt` — 提示词生成器（按类型分流） | ## 执行卡 · 提示词（Agent 必读） | true |
| `draw.ordinary` | 100 | 以上都不是 | `pmem-draw` | ## 二、标准执行流程（Step 1 ~ Step 3） | ## 零点五、开画前强制 route（与总控… + ## 执行卡 · 出图闭环（Agent 必读… + ## 记忆静默 / 履历可见（Agent 必… | true |

## unroutable_headings

（无）

## section_cut

ok：Icon Mode 互不吞并且 pack 含清单；draw.clone/variant/multi/key/ordinary 的 `slice_route_body` 含 reasonableness/闭环。
