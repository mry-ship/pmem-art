## 三、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge）

续轮垫图跟审图打印和 `converge next`：默认仍垫最初参考，改点只写进提示词；只有打印写明垫第几轮成图时，才垫那张成图。

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

### B5：关键图标最多3轮闭环（可选·默认跳过）
用户点名某枚「不对」或一致性不过时才开；垫最初 style-spec/样张；**禁止**对整套每枚开闭环：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module brand.WorldStyle --route-id icon.b
python3 pmem_art.py reasonableness review --id <session> --skill icon.b \
  --draft "<草稿>" --revised "<线宽/端点/清单写清的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;stroke_consistency=ok"
然后：generate → judge →（不到线继续，最多3轮）→ finish（标明是否 ≥9.5）
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

## 交件可见（出图结算 · Agent 必读）

**硬规矩**：只要本趟交了图（闭环任一轮、终稿、拆层散图、审图对象、锁风样张、归档清单等），结算必须先贴一张 Markdown **可点单图表**，再对表内每一张 `Read` 贴进对话。禁止只列文件名、禁止只交拼板/HTML、禁止「路径在目录里自己点」。

链接格式：相对仓库根，形如 `[第2轮](.memory-art/converge/boards/<id>/images/r2.jpg)` 或 `[01-bg](assets/<job>/new/01-bg.png)`。表头按交付类型选列，至少含「名称/槽位」+「可点图」。

### 闭环出图（跑过 `converge`）
1. **过程图拼板**：Read `process_sheet.jpg` 贴进对话。
2. **轮次单图表**：贴 finish 打印的表（轮次 × 分数 × 可点图）；也可用 `rounds.md`。
3. **逐张 Read**：表里每一轮原图各 Read 一次。
4. **本次耗时**：finish 报告末行「本次耗时」原样写出。
5. **中途每轮**：每次 `judge` 后立刻贴/更新可点表（至少本轮一行）并 Read 本轮原图；不要等 finish 才第一次给可点单图。

禁止只交拼板。禁止只甩 HTML。

### 四格与防污染（执行时必读）
四格不进路由句。必须保持、可以变化、明确禁止、交付规格只写 `contract set --keep --vary --forbid --spec`，标明原话或推断。禁止写入 `--canonical`。普通图用「题材不变」，禁止写「不换题材」。合同里的升级、一组、多张不得改技能。首轮提示词和后续修改只服从四格；聊天不是第二份需求；用户改口就用最新原话重写四格。
记忆只辅助。当前原话和四格优先于历史记忆。候选红线、没写 trust 的条目、旧任务主体、构图、档序和完整提示词不进提示词。已确认红线去掉旧任务目标，与明确禁止冲突则排除。研发 `.memory` 不进美术提示词。界面不继承合成梯玩具货柜缺省。
未点名接续只垫 `assets/refs/`、`downloads/`、`assets/skill_*/refs/`。禁止垫 out、phase1、关系稿、`.memory-art/converge` 过程板。垫图只取样式；只有用户说优化这张图才写原图不足。双参考像素同框仍硬停。最多 3 轮。

### 非闭环多图（拆层 / 审图 / 锁风样张 / 归档等）
同样强制可点单图表 + 逐张 Read。拆层须含叠回整图、幽灵对比、全部 `new/*.png`（有 `layers.md` 直接贴）。纯文字交付（提示词、无附图教练）不必出表。

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示见「交件可见」：必出**可点单图表** + Read 每一张图 +（闭环时）拼板与**本次耗时**。若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入；禁止只甩 HTML。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。