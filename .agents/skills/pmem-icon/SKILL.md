---
name: pmem-icon
description: 仅当玩家点名图标，或生图分流判成桌面图标、SVG 图标集、游戏道具格时使用。A/B/C 不混用。不要用来画普通插画或合成梯。(A) iOS/Android 1024×1024 App Icon 桌面启动图标母版（满幅直角出图+72%~80%圆角安全区+多尺寸导出矩阵+深浅色自适应）；(B) jezweb 式一致化 SVG 矢量图标集；(C) 游戏道具 64/128/256px 透明底栅格图标。全部支持 converge generate 与 converge judge 两步分离，以及动态阈值收敛闭环。
---

# `/pmem-icon` — jezweb 式一致化图标集 / SVG 取向生成

只在玩家点名图标，或 `/pmem-draw` 判成「图标」之后执行。先分 A/B/C，三条不混用。单张「按这张画风换一个新道具」走 `/pmem-draw` 的克隆合同，不在这里做成一整套。

## 怎么用（复制即用）
```text
/pmem-icon Mode A：iOS 1024 满幅直角 App Icon——青瓷记账应用，中心单枚立体青釉金币流光符号，落在 75% 安全区，无字无烤圆角
/pmem-icon Mode C：背包道具格 1:1——切面玻璃治疗药水+软木塞金丝叶饰，厚剪影棚拍光，暗 vignette 透明友好
/pmem-icon Mode B：24px Clean SVG 导航+背包一套（home settings inventory craft map quest），统一 stroke/viewBox，输出 style-spec 与 preview.html
/pmem-icon [拖入品牌样张] 按这个线宽与圆角补齐：phone email location
```

## 原理（截图摘要）
1. 先锁 **style-spec** → 2. SVG 硬规则 → 3. 分批生成 → 4. 交付 preview → 5. 关键枚 **Warm-Start + 最多 4 轮 ≥9.6** → 6. 反思写进记忆，要看报告再用 /pmem-coach

你现在运行在 **pmem-art 图标集模式**（对标 jezweb `icon-set-generator`）：先锁 **一份 style-spec**，再批量生成，保证 stroke、圆角、视口、视觉重量一致——**禁止**从 Lucide/Heroicons 随便拼一套「看起来差不多」的通用库图标冒充项目定制集。

---

## 一、三大模式分流（入口只有 `/pmem-icon`，按需求进对应分节，严禁串味）
- **【Mode A · App Icon 1024 母版】**（手机桌面启动图标 / iOS App Store / Android Adaptive / 产品 Logo）→ 直接跳至下方 **「## 二之二、Mode A：App Icon 1024×1024 母版专项」**（满幅直角 + 72%–80% 安全区 + 微立体光影，不用 SVG 规则）。
- **【Mode B · 24px 线性 SVG 图标集】**（网页 / App 导航栏 / HUD 矢量图标）→ 执行下方 **「## 二、Mode B：一致化 SVG 矢量图标集流程」**（只用 `currentColor` + 统一 stroke/viewBox）。
- **【Mode C · 游戏道具栅格图标】**（背包 64/128/256px 透明底 PNG 道具）→ 执行下方 **「## 二之三、Mode C：游戏道具透明底栅格图标」**（锁描边/色板/投影，不用 SVG 代码）。

## 二、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge）

### Step 1：理解项目与图标清单
收集：行业/项目气质、品牌色（即使 SVG 用 `currentColor` 也影响线型选择）、大约数量。
按组建议清单（可让用户增删）：
- Navigation / Communication / Trust / Actions / Industry-Specific（或游戏：Inventory / Combat / Status / Crafting）

### Step 2：锁定 Style Spec（生成前必须确认）
推荐预设起步：

| Preset | 适用 | Stroke | Caps/Joins | Corners |
|--------|------|--------|------------|---------|
| Clean | 多数业务站 | 1.5px | round/round | 2px |
| Sharp | 科技/硬核 | 1.5px | square/miter | 0px |
| Soft | 亲和/休闲 | 2px | round/round | 4px |
| Minimal | 编辑/优雅 | 1px | round/round | 0px |
| Bold | 高识别/无障碍 | 2.5px | round/round | 2px |

写入 `icons/style-spec.json`（含 grid/viewBox、strokeWidth、linecap、linejoin、padding、opticalBalance、icons[]）。

### Step 3：SVG 硬规则（整套必须统一）
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="{grid}" height="{grid}"
  viewBox="0 0 {grid} {grid}" fill="none" stroke="currentColor"
  stroke-width="{strokeWidth}" stroke-linecap="{…}" stroke-linejoin="{…}">
  <!-- paths -->
</svg>
```
1. **只用 `currentColor`**，禁止写死 `#000` / `blue`
2. **同一 viewBox**、同一根节点 stroke 属性
3. 无根节点 transform；无无用 id/class
4. 坐标最多 2 位小数；保持 padding；视觉居中（光学校正）
5. 路径尽量少；简单图标略加重以平衡视觉重量

图标 B 的正式分是加权调和平均。原来四项占 75%，无瑕疵占 25%，盲评。笔画多不加分。补进已经锁好的 style-spec，沿用原预设和原 viewBox。

- **笔画一致**：同一 viewBox、线宽、端点、拐角，只用 currentColor
- **视觉重量**
- **留白与光学居中**
- **24px 能对上功能**

一套里线宽或拐角混用，或目标尺寸认不出，不能停，正式分改取该维（低于 8.0）。示例：`笔画一致8.6/视觉重量8.4/留白8.5/功能识别8.8`

### 二之三、Mode C：游戏道具透明底栅格图标（64/128/256px PNG，非 SVG）
若用户要的是 **游戏道具栅格图标**：先锁「线宽/圆角/色板/投影」style-spec，再批量生成透明底 PNG。关键单枚用 `converge` 跑最多 4 轮，合格线 ≥9.6。

正式分是加权调和平均。原来三项占 75%，无瑕疵占 25%，盲评。透明底和无字仍是门槛。交付文件要有 alpha，白底和品红底不算透明底。

- **剪影识别（30%，也是门槛）**：64px 仍能认出，居中
- **描边色板（20%）**
- **棚拍光（20%）**
- **透明底（15%，只做门槛）**、**无字（15%，只做门槛）**：脏底，或出现任何字（含等级字），不能停

剪影认不出同样不能停。门槛低于 8.0 时正式分改取该维。示例：`剪影识别8.6/描边色板8.4/棚拍光8.5/透明底9.0/无字9.2`

### Step 4：分批生成（约每批 5 个）+ 一致性审查
每批完成后检查：stroke 是否漂移、圆角是否混用、有无图标明显偏轻/偏重、是否贴边。
全部完成后生成：
```
icons/
├── style-spec.json
├── preview.html      # 含 1x/2x 与深色底对比，内联 SVG
├── home.svg
└── …
```

### Step 5：关键图标 4轮9.6 收敛（可选）
用户点名某枚「不对」或一致性审查不通过时，每一轮垫最初的风格参考或 style-spec 样张，不垫上一轮成图：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module brand.WorldStyle
# 生成 → 自评 → converge generate / converge judge → finish
```

### Step 6：沉淀
```bash
python3 pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module brand.WorldStyle --kind art_decision
python3 pmem_art.py ingest icons/preview.html -p "icon set preview" --apply   # 若适用
```

## 二之二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标）

当用户要求制作 **App Icon / 手机桌面图标 / iOS 启动图标 / Android 自适应图标 / 产品 Logo 图标** 时，自动切换至 **App Icon 专项模式**：

### 1. 1024×1024 满幅直角母版与系统圆角安全区铁律
- **严禁预裁透明圆角**：母版必须输出 **`1024×1024` 满幅直角正方形（Full-bleed Square PNG，无 Alpha 透明缺角）**，防止系统套用 iOS 超椭圆（Superellipse Squircle）或 Android Adaptive 遮罩时露出黑边/白边裂隙。
- **核心图形安全区（Center 72%–80% Safe Zone）**：核心主符号（Hero Glyph）必须收束在画布中心 **`72%–80%`（约 `740×740 px`）安全圆/超椭圆内**，四周留出充足呼吸负空间，绝不贴边。
- **零细碎文字红线**：App Icon 严禁堆砌 Slogan、副标题或复杂多角色场景；只保留 **1 个高辨识度核心记忆符号**，确保缩放到 `29×29 px`（设置页）与 `60×60 px`（通知栏）时依然一眼认出。

### 2. 光学微立体质感与光影层次（Tactile Material & Lighting）
- **三层景深结构**：① 底板环境渐变层（70% 主色）→ ② 中心主符号微倾体块层（20% 辅色 + 柔和接触阴影 Contact Shadow）→ ③ 顶部 45° 高光切角边缘（Top-Edge Specular Rim，10% 点缀色）。
- **支持 iOS 18+ 三态适配**：输出标准浅色版（Light）、深色模式版（Dark Mode 深邃底板+自发光边缘）与单色着色版（Tinted 单通道明度层次）。

### 3. 多尺寸导出矩阵与 `app-icon-preview.html`
通过 `converge generate` 与 `converge judge` 分两步收敛出 `1024×1024` 母版后，自动导出标准尺寸包：
- **iOS 矩阵**：`1024×1024` (App Store)、`180×180` (@3x Home)、`167×167` (iPad Pro)、`120×120` (@2x)、`60×60` (Notification)、`29×29` (Settings)
- **Android / 桌面矩阵**：`512×512` (Play Store)、`192×192` (xxxhdpi Foreground/Background)

### 4. App Icon 审图（五项加无瑕疵，加权调和平均；无瑕疵占 25%，盲评。母版分够了，Light / Dark / Tinted 或尺寸矩阵没齐，不能停）
识别度或安全区低于 **8.0** 时，正式分改取该维，不能停。

1. **小尺寸识别（25%）**：一个主符号；缩到 29px 和 60px 仍是同一个剪影。
2. **安全区（25%）**：1024 满幅直角，不预裁圆角；主体在中心 72%–80%；不贴边。
3. **光影质感（20%）**：底板、符号、顶缘高光；接触阴影；不要廉价塑料。
4. **深浅色 / 多尺寸（15%）**：Light / Dark / Tinted；导出尺寸不糊成一团。
5. **色板纯粹（15%）**：70-20-10；没有口号、小字、杂物。

```bash
python3 pmem_art.py converge start --session appicon --module brand.WorldStyle --scale high --goal "iOS 1024x1024 App Icon: 青瓷质感记账应用，中心单枚立体青釉金币流光符号"
python3 pmem_art.py converge generate --session appicon --round 1 --image app_icon_r1.png --prompt "..."
python3 pmem_art.py converge judge --session appicon --round 1 --image app_icon_r1.png \
  --dims "识别度9.6/安全区9.7/光影质感9.5/多尺寸合规9.6/色板纯粹9.7"
```

## 三、交付检查清单
- [ ] 全部 SVG 同 viewBox / stroke-width / linecap / linejoin
- [ ] 全部 `currentColor`
- [ ] 视觉重量平衡、padding 一致、光学居中
- [ ] 文件名 kebab-case；`preview.html` + `style-spec.json` 齐全
- [ ] 若跑了收敛：默认展示每轮评分/不足/改点 + 胜出图（只要终稿用 --quiet）

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮六维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
