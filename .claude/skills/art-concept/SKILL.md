---
name: art-concept
description: 【截图可见·必读】/pmem-concept 与 /art-concept（原画/概念图/Key Art）与 /pmem-draw 一样，强制执行「最多8轮、合格线≥9.6分」闭环自评收敛：生1张→五维打分+指出不合理处→展示不足与改点→<9.6则叠加修正继续生→达标即停或满8轮挑最高分→默认展示评分履历并沉淀记忆。触发例：「/pmem-concept 画一张青瓷废土主视觉Key Art」「/art-concept [附参考] 同氛围气氛图」。Prompt 采用 ZHO/Yolain/Comfy-FLUX 式完整自然语言句（主体靠前、正向写排斥项）。
---

# `/pmem-concept`（别名 `/art-concept`）— 原画 / 概念图 / Key Art

> ⚠️ **【强制闭环 · 与 `/pmem-draw` 同等】**  
> 本技能生成原画/概念图/Key Art 时，**必须**跑满同一套收敛规则：  
> **最多 8 轮生图 · 合格线 `≥ 9.6 / 10.0` · 未达标叠加修正继续生 · 满 8 轮挑全阶段最高分 · 每轮展示评分/不足/改点 · `finish` 默认打印履历并写记忆（`--quiet` 只要终稿）**。  
> **禁止只生一张图就交差**（除非第 1 轮真实严苛评分就 ≥ 9.6）。

## 怎么用（复制即用）
```text
/pmem-concept 画一张东方青瓷废土的主视觉 Key Art，宽幅海报，电影感侧逆光
/art-concept 生成一张浮空遗迹黄昏气氛概念图，青瓷白+墨蓝+鎏金
/pmem-concept [拖入参考图] 保持构图与色板，画一张同世界观角色登场 Key Art
```

## 原理（截图摘要）
1. **Warm-Start + 与 draw 同等 8×≥9.6** → 2. `search`/口味召回 → 3. **FLUX 完整句** → 4. 垫图解构 → 5. `converge`（每轮摊开评分履历） → 6. `finish` 打印履历 + 记忆静默写入

你现在运行在 **pmem-art 原画 / 概念图 / Key Art 模式**（对标 ZHO Comfy-FLUX 与 Yolain 等 FLUX 系提示法）：用 **完整自然语言句子** 描述成片，**主体与构图靠前**；FLUX 系几乎无有效负向 Prompt，排斥项用正向措辞写进正文。

---

## 一、适用场景
- 主视觉 Key Art / 宣传海报 / 场景气氛图 / 角色概念设定 / 封面插画
- 需要电影感光影、叙事构图、高完成度单帧，而非 UI 切图或 SVG 图标

## 二、FLUX 系 Prompt 写法（必须遵守）
1. **完整句，不要纯 tag 堆砌**；T5/CLIP-L 对句子更友好。
2. **权重靠前**：先写主体与动作，再场景，再风格/光影/色板，再画幅与成片要求。
3. **无负向列表**：把「不要霓虹紫」写成「干净的青瓷白与墨蓝，无霓虹」。
4. **可选结构模板**：
   ```
   [主体与动作]。[场景与空间关系]。[光影与时段]。[材质与画风]。
   [色板：主色…辅色…点缀…]。[构图/景别/画幅]。[成片质量：边缘清晰、无水印无文字…]
   ```

## 三、标准流程（Memory → Prompt → Converge）

### Step 0：垫图（可选）
若用户丢入参考图：输出构图/色板 HEX/光影/笔触解构，写入 `converge start --ref-image … --ref-analysis …`。

### Step 1：召回记忆并开收敛会话
```bash
python3 pmem_art.py search --module <scene.|character.|brand.模块>
python3 pmem_art.py converge start --goal "<概念图目标>" --module <模块> [--scale low|medium|high|recompose] [--recompose-dir "…"] [--ref-image …] [--ref-analysis …]
```

### Step 2：最多 8 轮自评收敛（合格线 `>= 9.6`）
每轮：
1. 用上一轮缺陷的 **正向叠加修正** 重写完整句 Prompt（仍禁止只堆 negative tags）。
2. 生成 **1 张** 概念图 / Key Art。
3. **Absolute-5D** 严苛打分（有 Key→API；无 Key→本模型检查表；**禁止**像素尺 8.50 早停）+ 说出合理处与不合理处 → `converge generate` 然后 `converge judge`。
4. `>= 9.6` 立即停；`< 9.6` 且未满 8 轮则继续；满 8 轮挑最高分。

**概念图五维侧重（`--dims` 必须可被 `parse_5d_dims` 解析，否则本轮记 0 分）**：
主用 Absolute-5D：`构图x/光影x/透视x/质感x/风格x`（每维 0–10）。
评判侧重：构图→叙事机位与层次；光影→电影感侧逆/体积光；透视→空间纵深；质感→空气介质与材质可读；风格→色板与 Key Art 完成度。
示例：`--dims "构图9.2/光影9.0/透视8.8/质感8.9/风格9.1"`。
旧侧重串（`风格色板/构图叙事与透视/光影材质/红线合规/氛围意图还原`）现仍可解析为兼容加和尺，但**新会话请统一写 Absolute-5D**，以便与 `/pmem-draw` 履历直接对比。

### Step 3：结算与沉淀
```bash
python3 pmem_art.py converge finish
```
向用户默认展示：每轮审图卡（五维分/不足/改点）+ 胜出图 + 全轮评分履历；只要终稿时用 `--quiet`。

## 四、与 `/pmem-draw` 的分工
- **`/pmem-draw`**：通用单图收敛（角色立绘、道具、单件 UI 等）
- **`/pmem-concept`**：专门服务 **概念图 / Key Art / 气氛图**，强制 FLUX 式完整句 Prompt 与叙事构图标准


## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
