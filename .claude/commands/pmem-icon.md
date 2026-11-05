---
description: 【出图一轮交件·批量优先】iOS/Android App Icon + SVG 图标集 + 游戏道具栅格（pmem-art）
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
- **Mode A**：满幅直角母版 → 安全区单符号 → 尺寸矩阵；默认只交 **Light 母版**（出图一轮交件）；Dark/Tinted **仅点名才另出**
- **Mode B**：锁 style-spec → SVG 硬规则 → 分批生成 → preview（对标 jezweb）；关键枚闭环默认不开
- **Mode C**：锁道具格 style-spec → 透明底 PNG **只批量**；关键枚闭环默认不开
先分 A/B/C，再进对应节；反思写进记忆，要看报告再用 /pmem-coach。

### 耗时闸（出图一轮交件·必守）
- **名字含义**：只限生图轮次=1；style-spec/批量预览/清单仍要做。
- **B/C 批量**：整套一次出齐 → 肉眼/清单一致性审查（**不算** converge 叠轮）；**禁止**默认逐枚 converge。
- **关键枚闭环**：仅玩家点名某枚翻车；开则生1→judge1（CLI `max_rounds=1`），finish 标明是否 ≥9.5。
- **Mode A 三态**：**禁止**在无可靠导出/上色工具时口头说「Dark/Tinted 已派生齐」。默认交付 = Light 母版 + 尺寸矩阵；玩家点名 Dark 或 Tinted 时再各开一轮出图。

---

## 一、三大模式分流（入口只有 `/pmem-icon`，按需求进对应分节，严禁串味）
- **【Mode A · App Icon 1024 母版】** → 只读下方 **「## 二、Mode A：…」**（满幅直角 + 72%–80% 安全区；不用 SVG 规则）。
- **【Mode B · 24px 线性 SVG 图标集】** → 只读下方 **「## 三、Mode B：…」**（`currentColor` + 统一 stroke/viewBox）。
- **【Mode C · 游戏道具栅格图标】** → 只读下方 **「## 四、Mode C：…」**（透明底 PNG；不用 SVG 代码）。
A/B/C **标题并列**，禁止把 C 嵌进 B、把 A 甩到 B 的 Step 之后。读错节 = 串味。

## 二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标）

当用户要求制作 **App Icon / 手机桌面图标 / iOS 启动图标 / Android 自适应图标 / 产品 Logo 图标** 时走本节约。

### A1. 1024×1024 满幅直角母版与系统圆角安全区铁律
- **严禁预裁透明圆角**：母版必须输出 **`1024×1024` 满幅直角正方形（Full-bleed Square PNG，无 Alpha 透明缺角）**，防止系统套用 iOS 超椭圆或 Android Adaptive 遮罩时露出黑边/白边裂隙。
- **核心图形安全区（Center 72%–80% Safe Zone）**：核心主符号收束在画布中心 **`72%–80%`（约 `740×740 px`）** 内，四周留呼吸负空间，绝不贴边。
- **零细碎文字红线**：只保留 **1 个高辨识度核心记忆符号**；缩放到 `29×29` / `60×60` 仍一眼可认。

### A2. 光学微立体质感与光影层次
- **三层景深**：① 底板环境渐变（70% 主色）→ ② 中心主符号微倾体块（20% 辅色 + 接触阴影）→ ③ 顶部 45° 高光切角（10% 点缀色）。
- **iOS 18+ 三态**：默认只保证 **Light 母版**过关。Dark / Tinted **仅玩家点名**才另开 converge（各出图一轮）；没有点名就不要交假齐套，也不要写「已派生」。

### A3. 多尺寸导出与 `app-icon-preview.html`
母版收敛后导出：iOS `1024/180/167/120/60/29`；Android/桌面 `512/192`（导出几乎零墙钟，勿当成再生图轮次）。

### A4. App Icon 审图与命令
识别度或安全区低于 **8.0** 时正式分改取该维，不能停。维：小尺寸识别 / 安全区 / 光影质感 / 深浅色·多尺寸 / 色板纯粹（再加无瑕疵盲评，占 25%）。

**App Icon 多维透镜（通用）**：明细见 `docs/APPICON_MULTI_LENS.md`——①栅格体验；②小尺寸去色仍认；③符号权重 P0 英雄撑满；④满幅直角 + 72%–80% 安全区；⑤色 70/20/10；⑥一主光、形先于质；⑦同品类上架图标气质（非泛插画海报）。缺画风时 revised 必须写同品类顶级上架图标气质。空喊「高级」却剪影糊 → 识别度或安全区 <8.0 不能停。

```bash
pyw -3 -u pmem_art.py converge start --session appicon --module brand.WorldStyle --scale high --route-id icon.a --goal "iOS 1024x1024 App Icon: 青瓷质感记账应用，中心单枚立体青釉金币流光符号"
pyw -3 -u pmem_art.py reasonableness review --id appicon --skill icon.a \
  --draft "<草稿>" --revised "<单符号+72%-80%安全区+满幅直角无字的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;safe_zone=ok;single_symbol=ok;full_bleed_no_round_mask=ok"
pyw -3 -u pmem_art.py converge generate --session appicon --round 1 --image app_icon_r1.png
pyw -3 -u pmem_art.py converge judge --session appicon --round 1 --image app_icon_r1.png \
  --dims "识别度9.6/安全区9.7/光影质感9.5/多尺寸合规9.6/色板纯粹9.7/无瑕疵9.5"
# CLI 出图一轮交件：max_rounds=1；judge 后 finish，并标明是否 ≥9.5
```

## 三、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge）

### B1：理解项目与图标清单
收集：行业/项目气质、品牌色、大约数量。按组：Navigation / Communication / Trust / Actions / Industry-Specific（或游戏 Inventory / Combat / Status / Crafting）。

### B2：锁定 Style Spec（生成前必须确认）

| Preset | 适用 | Stroke | Caps/Joins | Corners |
|--------|------|--------|------------|---------|
| Clean | 多数业务站 | 1.5px | round/round | 2px |
| Sharp | 科技/硬核 | 1.5px | square/miter | 0px |
| Soft | 亲和/休闲 | 2px | round/round | 4px |
| Minimal | 编辑/优雅 | 1px | round/round | 0px |
| Bold | 高识别/无障碍 | 2.5px | round/round | 2px |

写入 `icons/style-spec.json`（含 grid/viewBox、strokeWidth、linecap、linejoin、padding、opticalBalance、icons[]）。

### B3：SVG 硬规则（整套必须统一）
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

图标 B 正式分：笔画一致 / 视觉重量 / 留白与光学居中 / 24px 功能识别（四项 75%）+ 无瑕疵 25%。线宽或拐角混用、目标尺寸认不出 → 正式分改取该维（<8.0）不能停。judge 示例：`--dims "笔画一致8.6/视觉重量8.4/留白8.5/功能识别8.8/无瑕疵8.7"`。

**图标 B 短透镜**：①同一 stroke/viewBox/端点拐角；②光学重量接近；③padding 一致；④24px 可认；⑤只用 currentColor；⑥禁止拼公开图标库冒充定制集。

### B4：分批生成（约每批 5 个）+ 一致性审查
检查 stroke/圆角/重量/贴边。全部完成后生成：
```
icons/
├── style-spec.json
├── preview.html
├── home.svg
└── …
```

### B5：关键图标出图一轮交件（可选·默认跳过）
用户点名某枚「不对」或一致性不过时才开；垫最初 style-spec/样张；**禁止**对整套每枚开闭环：
```bash
pyw -3 -u pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module brand.WorldStyle --route-id icon.b
pyw -3 -u pmem_art.py reasonableness review --id <session> --skill icon.b \
  --draft "<草稿>" --revised "<线宽/端点/清单写清的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;stroke_consistency=ok"
然后：generate → judge → finish（CLI max_rounds=1；标明是否 ≥9.5）
```

### B6：沉淀
```bash
pyw -3 -u pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module brand.WorldStyle --kind art_decision
pyw -3 -u pmem_art.py ingest icons/preview.html -p "icon set preview" --apply
```

## 四、Mode C：游戏道具透明底栅格图标（64/128/256px PNG，非 SVG）

先锁「线宽/圆角/色板/投影」style-spec，再**批量**生成透明底 PNG 做 preview。  
**关键枚 converge 默认禁止**：仅玩家点名某枚不对、或一致性审查不过时才开；开则出图一轮交件（CLI `max_rounds=1`，标明是否 ≥9.5）。**禁止**默认对背包每一格开闭环。
```bash
pyw -3 -u pmem_art.py converge start --session <icon_c_id> --goal "道具格：<name>" --module brand.WorldStyle --route-id icon.c
pyw -3 -u pmem_art.py reasonableness review --id <icon_c_id> --skill icon.c \
  --draft "<草稿>" --revised "<厚剪影+透明底+棚拍光+无字的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;silhouette_read=ok;transparent_friendly=ok"
# 然后：converge generate → judge → finish（均带 --session <icon_c_id>）
```

正式分：剪影识别 30%（门槛）/ 描边色板 20% / 棚拍光 20% / 透明底 15%（门槛）/ 无字 15%（门槛）；无瑕疵盲评同库（展示六维时须带上）。judge 示例：`--dims "剪影识别8.6/描边色板8.4/棚拍光8.5/透明底9.0/无字9.2/无瑕疵8.8"`。交付须真 alpha；白底/品红底不算透明底。门槛 <8.0 → 正式分改取该维。

**同店气质对齐（缺风格时强制）**：未点名画风且无风格参考时，写同品类顶级道具格气质（先认品类；禁止非休闲硬套软塑胶 merge）。同任务已有合成梯/`surface` 必须复用同一句。禁止垫竞品像素抄脸。

**图标 C 短透镜**：①厚剪影 64px 可认；②真 alpha；③品类主光+接触影；④描边/色板/投影锁死；⑤无字无场景；⑥形先于质；⑦优先复用同店 surface。

## 五、交付检查清单（按模式分流，禁止混用）

### Mode A
- [ ] 1024 满幅直角，未预裁圆角蒙版
- [ ] 主符号在 72%–80% 安全区；无字
- [ ] Light 母版 + 尺寸矩阵齐；Dark/Tinted 仅点名才有，未点名勿写已齐套
- [ ] 跑了收敛则展示评分履历并标明过线/未过线（只要终稿用 --quiet）

### Mode B
- [ ] 全部 SVG 同 viewBox / stroke-width / linecap / linejoin
- [ ] 全部 `currentColor`
- [ ] 视觉重量平衡、padding 一致、光学居中
- [ ] 文件名 kebab-case；`preview.html` + `style-spec.json` 齐全
- [ ] 若跑了收敛：展示每轮评分/不足/改点 + 胜出图

### Mode C
- [ ] 真 alpha 透明底；厚剪影 64px 可认
- [ ] 套件描边/色板/投影一致；无字
- [ ] 品类主光 + 接触影；无场景插画
- [ ] 关键枚若收敛：评分履历可见

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮六维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
