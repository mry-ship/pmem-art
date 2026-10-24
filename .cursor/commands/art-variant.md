---
description: 同角色/同资产跨画风分叉（水彩/Q版/像素）与表情动作差分（pmem-art）
---

# `/pmem-variant`（别名 `/art-variant`）— 跨画风分叉与表情/动作差分生成

当用户希望把已有角色/物件衍生出新画风（如「把 Astra 做成 Q 版贴纸 / 水彩概念图」）或做差分（如「生成愤怒/惊讶表情差分」「生成 4 帧挥刀序列帧」）时执行：

1. **读取父模块核心锚点**：
   - 运行 `python3 pmem_art.py search --module <父模块，如 character.Astra>`。
   - 锁定不可改变的**人设核心识别特征**（发色、瞳色、标志性配饰如左眼黄铜星盘义眼、主色板）。
2. **确定子模块与规格适配**：
   - 画风分叉：如 `character.Astra.Chibi`（2~3头身、允许大头萌化）、`character.Astra.Watercolor`（允许非透明纸本纹理底 `alpha_required: false`）。
   - 差分/动画：如 `character.Astra.Expressions`（严格锁死五官比例与底图机位）、`anim.Astra` 或 `vfx.*`（整除序列帧网格 + 透明底）。
3. **调用自评收敛生图并独立归档**：
   - 按 9.5 分标准生成与自评，完成后运行 `python3 pmem_art.py ingest <新图路径> -p "<含角色名+画风/差分词的Prompt>" --apply` 自动创建子模块并归位。
