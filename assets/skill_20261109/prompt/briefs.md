# 提示词方案 · 妖精花园休闲（多类型代表）

**判定类型：`多类型代表 brief 包` · 依据：玩家要一批覆盖 UI / 图标 A·B·C / merge / 原画的提示词，非单类 2～4 套同型分叉 · 将交给：对应 `/pmem-…`（见各方案）**  
**route 校正（以 CLI 为准）：`route_ids=['prompt.write']` · banner：【按 提示词生成器：按交付类型扩写可选方案 走了】· conversation=`skill1109-prompt` · execute_ok=true**  
本支只写 brief，**不生图**。每套旁标注目标出图 `route_id=`。

## 听懂的交付

- **交付物**：妖精花园休闲主题的一套「可交出生图技能」的代表提示词（按类型各给代表，不混句式）。
- **已锁定**：题材=妖精花园；范围=UI + 图标三档 + 合成梯 + 原画；气质跟展陈参考包 `_refs/`（风格样张 / 角色 / 蘑菇道具 / 主菜单蛙感 / merge 整表版式 / App Icon 完成度）——**只抽气质，禁止垫像素抄构图**。
- **还晃**：具体角色发色瞳色未钉死 → 原画/UI 场景角色标「还不确定，可用参考妖精身份」；图标 B 清单可跟已有 `icon_b/style-spec.json` 十枚入口。
- **缺画风默认（按类型分系，禁止一律软塑胶）**：
  - UI → `ui.casual_hud`：上架截图密度、顶栏清晰、主 CTA 一眼最大、chrome 与场景同系
  - 图标 A → `icon.app`：单符号撑满 72%–80% 安全区、满幅直角
  - 图标 C / merge → `icon.prop` / `merge.cabinet`：软塑胶厚实、棚柔光短接触影、饱和友好、缩略可读（同店 surface）
  - 原画 → `keyart.store` + 可借 `watercolor.portrait` 纸纹飞白（跟风格样张，勿空喊史诗）

---

## 方案 A · 花园主页 · `route_id=ui.kit`

- **中文目标句**：竖屏或 9:16 休闲花园养成**主菜单概念稿**（concept-only）。对标品类=休闲花园/装修养成主页（气质参考蛙感主菜单分区，**未点名三消，禁止默套 Royal Match 头像|币|心|星骨架**）。分区：顶栏单行=头像珠 + 金币/钻石资源条 + 右上小设置；中部大场景露苔绿花园与远处妖精剪影（脸不被 chrome 压）；中下 P0 主任务一枚大圆角釉木「继续花园」CTA；底栏四～五枚同系导航（家园/背包/商店/任务/图鉴）。材质：浅木描边 + 柔釉按钮 + 短暖接触影；chrome 与场景同系，禁止海报飘钮与可读乱码字。商业完成度对标上架截图密度。
- **英文执行句**：Casual fairy-garden home menu concept (vertical/9:16), NOT Royal Match layout. Top single row: avatar bead + coin/gem bars + tiny settings. Mid: moss-garden scene with distant fairy silhouette, chrome clear of face. Lower-mid: one oversized glazed-wood rounded primary CTA “Continue Garden”. Bottom 4–5 same-family nav tabs (home/bag/shop/quest/bestiary). Soft wood outlines, glaze buttons, short warm contact shadows; chrome matches scene; no floating poster buttons, no readable gibberish text; store-screenshot casual-HUD finish.
- **本套侧重**：布局分区 / 主 CTA 权重（花园养成主页，非三消）
- **相对原话改了什么**：补齐屏幕类型、分区、控件层级、材质同系与禁止默套 RM
- **建议交给**：`/pmem-ui`

---

## 方案 B · 精灵符标 · `route_id=icon.a`

- **中文目标句**：妖精花园 App Icon **1024 满幅直角母版**（不烤圆角遮罩）。单符号英雄：一只超大精灵翼剪影抱一颗发光孢子蘑菇，落中心 **72%–80% 安全区**并尽量撑满；浅苔绿→蜜杏底板渐变，无字无场景无第二英雄。上左柔主光、短接触影；软立体玩具肤质但**形先于质**，60px 去色仍认翼+菇。对标同品类上架图标完成度（气质可参考 latte/jade 图标密度，禁止抄脸）。
- **英文执行句**：1024 full-bleed square App Icon master, sharp corners, no pre-baked mask. Single hero: oversized fairy-wing silhouette cradling one glowing spore mushroom, centered in 72–80% safe zone and filling it; moss-green to honey-apricot backdrop gradient; no type, no scene, no second hero. Soft top-left key, short contact shadow; soft-toy surface but silhouette-first; readable at 60px; top-store app-icon finish.
- **本套侧重**：单符号隐喻（翼+菇）/ 安全区撑满
- **相对原话改了什么**：钉死母版规格、安全区、禁字禁景、上架图标对标句
- **建议交给**：`/pmem-icon`（档 A）

---

## 方案 C · 线性导航 · `route_id=icon.b`

- **中文目标句**：**线性 SVG 功能图标集规格**（不是插画）。`viewBox=0 0 24 24`，stroke=2，round cap/join，约 4px 圆角语言，padding≈2，`currentColor`、fill=none；重量与光学平衡全套一致，24px 可认。清单：家园 / 背包 / 商店 / 任务 / 设置 / 图鉴 / 地图 / 浇水壶 / 嫩芽 / 精灵翼（与 `icon_b/style-spec.json` Soft 预设对齐）。隐喻跟花园操作，禁止拼公开图标库冒充。商业对标：休闲花园 HUD 导航——亲和圆角、轻视觉重量。
- **英文执行句**：Linear SVG icon set spec (not illustration): viewBox 0 0 24 24, stroke 2, round caps/joins, ~4px corner language, padding ~2, currentColor, fill none; consistent weight/optical balance; readable at 24px. Set: home, bag, shop, quest, settings, bestiary, map, watering-can, sprout, fairy-wings. Garden-action metaphors; Soft stroke preset; casual-garden HUD nav finish—friendly corners, light visual weight.
- **本套侧重**：统一 stroke 预设 / 入口清单
- **相对原话改了什么**：从「要图标」落到可交 `/pmem-icon` B 的规格句与清单
- **建议交给**：`/pmem-icon`（档 B）

---

## 方案 D · 蘑菇道具 · `route_id=icon.c`

- **中文目标句**：妖精花园背包**道具格** 1:1，真 alpha 透明底，无字无场景。主体=红白斑飞伞菇（可跟 `ref_prop_mushroom.png` 身份），厚剪影 **64px 可认**；棚拍左上主光、短暖接触影；软塑胶厚实圆润，角隅禁半透明毛边。与同店 merge `surface` 复用：**软塑胶厚实、棚柔光短接触影、饱和友好、货柜缩略可读**。不是场景插画，不是 App Icon。
- **英文执行句**：1:1 inventory prop icon, true alpha, no text no scene. Red-cream spotted toadstool (fairy-garden shop family), thick silhouette readable at 64px; soft top-left studio key, short warm contact shadow; soft-plastic rounded toy finish; clean opaque corners no fringe. Reuse same-shop merge surface: soft plastic, soft studio light, short contact shadow, saturated friendly, cabinet-thumbnail readable. Not a scene illustration, not an app icon.
- **本套侧重**：厚剪影 / 真 alpha / 与 merge 同 surface
- **相对原话改了什么**：钉死道具格合同与同店表面句，避免画成海报
- **建议交给**：`/pmem-icon`（档 C）

---

## 方案 E · 蘑菇升级 · `route_id=merge.ladder`

> **本套第一段是关系稿，不是八张插画 prompt。** 说通后再交给 `/pmem-merge-ladder`；默认 `delivery=overview_sheet`、`levels=8`（有格子参考则跟格数）。

- **链型提案**：`chain_mode=shop_ladder`（同族形变 / 同店货；非糖果可轻门，本题材走同店蘑菇升级）
- **家族基因**：红白斑伞菇 · 苔绿茎环 · 软塑胶玩具感
- **对标档序气质**：`merge.cabinet` / Merge Mansion–Travel Town–EverMerge 货柜——软塑胶厚实、棚柔光短接触影、饱和友好、棋盘缩略可读；版式气质可参考鸟类整表卡网，**禁止抄鸟**
- **中文关系稿（L1→L8）**：
  1. L1 小孢子球（原料，未开伞）
  2. L2 嫩芽菇钉（初露伞尖）
  3. L3 幼伞菇（小伞成形，斑点稀）
  4. L4 斑伞菇（伞面斑点清晰，茎环出现）
  5. L5 彩斑菇（斑点加密 + 微光孢子尘，犒赏材质首次）
  6. L6 双环菇（第二菌环 + 伞缘加厚）
  7. L7 宝盖菇（伞顶嵌一小颗蜜色晶露）
  8. L8 花园王菇（体量最大，晶露成簇但仍是单件伞菇，勿焊城堡）
  - 每档体量只大一圈；64px 邻档剪影不可复读；合两下可倒推；`surface` 全链同一句。
- **英文执行句（关系摘要）**：Fairy-garden spotted-mushroom shop_ladder L1 spore → L8 garden-king toadstool; same family genes; soft-plastic merge-cabinet surface; overview sheet default 8 cells; one object per cell; no castles welded; silhouette steps readable at 64px.
- **本套侧重**：升级叙事 / 犒赏曲线（关系先于出图）
- **相对原话改了什么**：把「要 merge 提示词」落成可过五问的关系稿 + surface
- **建议交给**：`/pmem-merge-ladder`（先 relation，再说通再出图）

---

## 方案 F · 花园原画 · `route_id=draw.key`

- **中文目标句**：妖精花园**上架 Key Art / 主视觉**，横幅约 16:9。黄昏蜜杏侧光穿过苔绿树冠，空气透视层层退远；前景一棵巨大斑伞菇与石径，中景一位花园妖精（身份可跟 `ref_character_fairy.png`，发色瞳色若未钉死标还不确定）半身回望，远景浮岛灯火如萤。媒介：湿画水彩纸纹飞白 + 软边结构仍连（对标 `watercolor.portrait` / 风格样张气质），商店截图级完成度（`keyart.store`）。**无 UI 控件、无可读乱码字、非货柜格拼贴**。主视觉记忆点=「黄昏花园里回头的妖精 + 巨菇剪影」。
- **英文执行句**：Store Key Art, ~16:9. Honey-apricot dusk side light through moss canopy with layered aerial perspective; foreground giant spotted toadstool and stone path; midground garden fairy (identity may follow character ref; hair/eye color TBD if unlocked) half-body looking back; distant floating-garden firefly lights. Wet watercolor paper tooth and soft edges with connected structure; store-screenshot key-art finish. No UI chrome, no readable gibberish, not a merge-cabinet sheet. Memory hook: dusk fairy glance + giant mushroom silhouette.
- **本套侧重**：机位叙事 / 水彩媒介 / 主视觉记忆点
- **相对原话改了什么**：钉死原画合同（无控件）、光色戏剧与商业完成度句
- **建议交给**：`/pmem-draw`（原画合同）

---

## 方案索引

| 字母 | 方案名 | 目标 route_id | 建议交给 |
| :--- | :--- | :--- | :--- |
| A | 花园主页 | `ui.kit` | `/pmem-ui` |
| B | 精灵符标 | `icon.a` | `/pmem-icon` A |
| C | 线性导航 | `icon.b` | `/pmem-icon` B |
| D | 蘑菇道具 | `icon.c` | `/pmem-icon` C |
| E | 蘑菇升级 | `merge.ladder` | `/pmem-merge-ladder` |
| F | 花园原画 | `draw.key` | `/pmem-draw` |

请回字母（可多选）或改口（例如「UI 其实要局内 HUD 不是主菜单」）。**点选前禁止开生图。**  
若之后出图：对该字母再跑  
`python3 pmem_art.py route --text "<选定方案>" --canonical "<该类型标准路由句>"`  
再进对应 `/pmem-…`；禁止只凭本技能自判直接 `converge start`。
