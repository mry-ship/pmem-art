# 风格锁定卡片 · style.lock

**【按 锁风格 走了】** `route_id=style.lock`  
锁定范围：`brand.WorldStyle`（项目级；未点名角色模块）  
样张：`assets/skill_20261112_suite/refs/ref_merge.png`（Gossip Harbor 真机海鲜 merge 棋盘）  
本步不生图。

> CLI `route` 因无附图触发 `artist_ask_style_ref` 询问；本趟 Suite 已点名 `style.lock` + 已读样张像素，近邻全票 `style.lock`，按点名执行并入库。

---

## 1. 色板（70 / 20 / 10）

| 角色 | 中文名 | HEX | 占比 | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| 主色 | 奶油沙岸 | `#F4C584` | ~70% | 浅色圆角卡、沙滩/木托盘底、货柜暖基调 |
| 辅色 A | 珊瑚龙虾红 | `#FF4D30` | ~12% | 龙虾/蟹等高识别海鲜主体 |
| 辅色 B | 港湾青 | `#48D1FF` | ~8% | 水面/泳具/UI 青蓝点缀（非霓虹） |
| 点缀 | 金币暖黄 | `#FFD700` | ~10% | 金币、合并星芒、高价值辉光 |

补充可读辅色（不改主比例）：冰盘冷白 `#F7FBFF`、柠檬黄 `#FFE566`、海草绿 `#3CB371`（仅作配菜点）。

---

## 2. 光影法则

- **主光**：左上偏暖棚光（约 10–11 点钟），色温偏暖白。
- **环境光**：浅青/天蓝天光从上方补一点冷边，避免死黑阴影。
- **高光**：块面釉面高光（软边、宽柔），道具呈「软立体玩具货柜」体积，不是摄影级湿润镜面。
- **合并反馈**：高档/合并瞬间可有暖金星芒与柔晕，克制、短促，禁止赛博霓虹环。
- **阴影**：干净接触影 + 浅 AO；禁止脏暗泥污、高对比明暗法。

---

## 3. 笔触与渲染

- 软立体 / 玩具货柜表面：圆润厚实、无硬描边、暖饱和。
- 边缘干净可缩略识别；64px 邻档剪影可分。
- 材质：糖釉感柔光釉面（跟真机货面），**勿**再灌缺省「软糖 SSS 长句」覆盖真机表面。
- 禁止：硬镜面 CGI、皮克斯硬塑、哑光黏土软塑胶 UI、厚黑描边、扁平矢量贴纸。

---

## 4. 正向风格词

圆润厚实 · 软立体玩具货柜 · 无硬描边 · 暖饱和 · 块面釉面高光 · 棋盘缩略可读 · 港湾海鲜同店色相 · 浅奶油圆角卡

## 5. 负向禁用词（Anti-Style）

硬镜面 CGI · 皮克斯硬塑 · 哑光黏土 · 软塑胶 UI · 厚黑描边 · 写实摄影摆盘 · 脏暗泥污阴影 · 赛博霓虹紫雾 · 灰雾废土 · 扁平矢量贴纸 · 油腻金属 · 指纹旧塑料 · 抄角色脸/标志/棋盘布局 · 抄 HUD/手指

---

## 6. 记忆写入路径

| kind | id / path |
| :--- | :--- |
| `art_decision` | `.memory-art/entries/brand.WorldStyle/CHAT20261112220940541DECISION.md` |
| `recipe`（垫 `ref_merge.png`） | `.memory-art/entries/brand.WorldStyle/CHAT20261112221006060RECIPE.md` |
| `style_redline` | `.memory-art/entries/brand.WorldStyle/CHAT20261112220939400REDLINE.md` |

同模块下一张开场必须带上已锁 HEX 与禁用词。

---

## 7. 可直接拿去生图的完整句子（风格句，不含构图抄袭）

Soft-sculpt casual merge toy-cabinet surface locked from Gossip Harbor seafood board: creamy shore base `#F4C584` (~70%), coral lobster red `#FF4D30` and harbor cyan `#48D1FF` (~20%), gold-coin accent `#FFD700` (~10%); warm upper-left soft key light with clean blocky glaze highlights; round thick silhouettes, no hard outlines, warm saturated shelf-readable props; forbid hard CGI mirrors, Pixar hard plastic, matte clay UI, thick black lineart, photoreal plating, muddy shadows, neon cyber purple, flat sticker vectors.
