## 执行卡 · 拆图层（Agent 必读）

1. 读原图 → 写 `assets/<job>/split_plan.json`（`id/name/z/crop/keep/remove/file`；玩家点名 N 层则 `modules` 含 bg 总数 = N）。
2. `setup` → 看 `_crops_guide.png` + `_crops/`：贴边切肢先扩框再 setup；框够大优先，禁止为过闸收框。
3. 背景优先 gpt-image-2.5；无通路再用 Cursor **不透明隔离底**（默认纯黑），禁止后抠。
4. `isolate` 并行抽未过线层（`--workers` ≤ `agent.max_parallel`，默认 4；双垫图：全主体 crop + `_ctx`）；出图硬锁样子/视角/风格，大小位置可漂。
5. `compose` → `gate` → `qa` → `emit`；脚印不过 → 重抽精灵或扩被点名边，禁止拧框凑比例。
6. 结算贴 `layers.md`（或等价可点表）并 `Read` 叠回整图 + 各层散图；`stack.html` 仅旁路。
7. 细则见下方「一次做对的流程 / 闸门与尺寸」；本地壳 `pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> …`。
8. 四格不进路由句。拆层不扩大题材。候选红线和旧任务主体不进提示词。细则见下方「四格与防污染」。

---

## 交件可见（拆层结算 · Agent 必读）

**硬规矩**：结算必须贴 **可点单图表**，再对表内每一张 `Read` 贴进对话。禁止只列目录、禁止只甩 `stack.html`。

1. 优先贴 `emit` 写出的 `layers.md`（叠回整图 + 幽灵对比 + 全部 `new/*.png` 的 Markdown 可点链接）。
2. 若无 `layers.md`，手写等价表：列「# / 名称 / 可点图」，链接相对仓库根，形如 `[01-bg.png](assets/<job>/new/01-bg.png)`。
3. 对表内每一张图（含 `_compose_mid.png`、`_compose_preview.png`、各层散图）各 `Read` 一次。
4. `stack.html` 仅作旁路预览，不能代替可点单图表。

### 四格与防污染（执行时必读）
四格不进路由句。必须保持、可以变化、明确禁止、交付规格只写 `contract set --keep --vary --forbid --spec`，标明原话或推断。禁止写入 `--canonical`。合同里的升级、一组、多张不得改技能。拆层只修边缘、遮挡补全和叠回还原，不另造数字阈值。
记忆只辅助。当前原话和四格优先于历史记忆。候选红线、没写 trust 的条目、旧任务主体、构图和完整提示词不进提示词。研发 `.memory` 不进美术提示词。
未点名接续只垫 `assets/refs/`、`downloads/`、`assets/skill_*/refs/`。禁止垫 out、phase1、关系稿、`.memory-art/converge` 过程板。垫图只取样式；只有用户说优化这张图才写原图不足。双参考像素同框仍硬停。最多 3 轮。