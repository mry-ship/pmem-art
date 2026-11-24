# atlas.file 展陈收口

**路由**：`atlas.file` · **banner**：【按 /pmem-atlas 走了】  
**会话**：`showcase-atlas-20261123` · **生图**：否

## 执行摘要

| 步骤 | 结果 |
|------|------|
| `classify-watch --apply` | 扫描 **116** 张未映射图；高置信 **自动入库约 36 条**（日志见 `classify-watch.log`）。长任务曾 **中断**，低置信仍为 candidate，未强行移动。 |
| `list` | 列出 **120** 个有内容模块（隐藏空壳 214）。 |
| `doctor` | 覆盖率 **78.4%**（297/379）；STALE **3**；孤儿 **82**；缺图锚点 **28**；见 `doctor.log`。 |
| `atlas` | 已生成 **`art-atlas.html`**（约 **9532.6 KB**，索引 **895** 张）。 |

## 打开工作台

请用浏览器访问（勿仅用 `file://` 双击 HTML）：

**http://127.0.0.1:27913/art-atlas.html**

或双击仓库根目录「打开工作台.cmd」。

## 代表归档（高置信入库，节选）

| # | 归位路径 |
|---|----------|
| 1 | `assets/scene/uikitpause/concept.png` |
| 2 | `assets/ui/thanksgiving/thanksgiving_merge_ui_ref.png` |
| 3 | `assets/ui/valentine/valentine_merge_ui_r1.jpg` |
| 4 | `assets/character/dogcollage20261117/final.jpg` |
| 5 | `assets/ui/dog/dog_chess_15_preview.jpg` |
| 6 | `assets/ui/ocean/ocean_chess_15_preview.jpg` |
| 7 | `assets/ui/r3/r3.jpg` |

完整 `place.to` 列表见 `classify-watch.log` 中 `"moved": true` 条目。

## 产物

- `RESULT.json` — 机读回传
- `atlas.log` / `list.log` / `doctor.log` — 本轮 CLI 输出
- 根目录 `art-atlas.html` — 刷新后的图谱工作台