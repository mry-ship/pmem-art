---
description: 【强制8轮≥9.5收敛】原画/概念图/Key Art（ZHO·FLUX式完整句Prompt）（pmem-art）
---

# `/pmem-concept`（别名 `/art-concept`）— 原画 / 概念图 / Key Art

> ⚠️ **【强制闭环 · 与 `/pmem-draw` 同等】**  
> 本技能生成原画/概念图/Key Art 时，**必须**跑满同一套收敛规则：  
> **最多 8 轮生图 · 合格线 `≥ 9.5 / 10.0` · 未达标叠加修正继续生 · 满 8 轮挑全阶段最高分 · 最终输出评分优劣总表并写入 `.memory-art`**。  
> **禁止只生一张图就交差**（除非第 1 轮真实严苛评分就 ≥ 9.5）。

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
python3 pmem_art.py converge start --goal "<概念图目标>" --module <模块> [--ref-image …] [--ref-analysis …]
```

### Step 2：最多 8 轮自评收敛（合格线 `>= 9.5`）
每轮：
1. 用上一轮缺陷的 **正向叠加修正** 重写完整句 Prompt（仍禁止只堆 negative tags）。
2. 生成 **1 张** 概念图 / Key Art。
3. 五维严苛打分 + 说出合理处与不合理处 → `converge round`。
4. `>= 9.5` 立即停；`< 9.5` 且未满 8 轮则继续；满 8 轮挑最高分。

**概念图五维侧重**：
1. 风格色板（2.5）2. 构图叙事与透视（2.5）3. 光影材质（2.0）4. 红线合规（1.5）5. 氛围/意图还原（1.5）

### Step 3：结算与沉淀
```bash
python3 pmem_art.py converge finish --apply
```
向用户展示：胜出图、全轮次评分表、最终 Prompt 全文、已写入的 recipe/redline。

## 四、与 `/pmem-draw` 的分工
- **`/pmem-draw`**：通用单图收敛（角色立绘、道具、单件 UI 等）
- **`/pmem-concept`**：专门服务 **概念图 / Key Art / 气氛图**，强制 FLUX 式完整句 Prompt 与叙事构图标准
