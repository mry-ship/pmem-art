# EXEC PACK icon.b

banner heading: ## 三、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge）
skill: pmem-icon
file: .cursor/skills/pmem-icon/SKILL.md

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

### B5：关键图标最多4轮闭环（可选·默认跳过）
用户点名某枚「不对」或一致性不过时才开；垫最初 style-spec/样张；**禁止**对整套每枚开闭环：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module brand.WorldStyle --route-id icon.b
python3 pmem_art.py reasonableness review --id <session> --skill icon.b \
  --draft "<草稿>" --revised "<线宽/端点/清单写清的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;stroke_consistency=ok"
然后：generate → judge →（不到线继续，最多4轮）→ finish（标明是否 ≥9.5）
```

### B6：沉淀
```bash
python3 pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module brand.WorldStyle --kind art_decision
python3 pmem_art.py ingest icons/preview.html -p "icon set preview" --apply
```

### Mode B
- [ ] 全部 SVG 同 viewBox / stroke-width / linecap / linejoin
- [ ] 全部 `currentColor`
- [ ] 视觉重量平衡、padding 一致、光学居中
- [ ] 文件名 kebab-case；`preview.html` + `style-spec.json` 齐全
- [ ] 若跑了收敛：展示每轮评分/不足/改点 + 胜出图

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮六维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。