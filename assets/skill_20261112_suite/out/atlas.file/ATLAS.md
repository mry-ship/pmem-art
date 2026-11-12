# `/pmem-atlas` · suite 收尾归档

## 做了什么

1. **`pyw -3 -u pmem_art.py classify-watch --apply`**
   - 扫描 `watch_dirs`：`assets` / `.cursor/generated` / `generated`
   - 未映射图：**314** 张
   - 其中 **suite (`assets/skill_20261112_suite/**`)** 高置信（≥0.78）入库并归位：**83** 张
   - 全库低置信候选保持原位（未强行移动）；suite 路径本趟全部命中高置信阈值，无 suite 低置信保留项
2. **`pyw -3 -u pmem_art.py list`**
   - 显示 **96** 个有内容/有资产模块（隐藏空壳 197）
3. **`pyw -3 -u pmem_art.py atlas`**
   - 已刷新：`art-atlas.html`（约 11.3 MB · 相对路径懒加载 · 索引 **824** 张）
   - 工作台：http://127.0.0.1:27913/art-atlas.html
   - 请用该 URL 或「打开工作台.cmd」，勿只双击 `file://` 打开 HTML

## Suite 归位摘要（按来源目录）

| 来源目录 | 入库张数 |
| :--- | ---: |
| `refs/` | 14 |
| `out/icon.a/` | 13 |
| `out/draw.ordinary/` | 9 |
| `out/ui.kit/` | 9 |
| `out/draw.key/` | 9 |
| `out/draw.multi/` | 8 |
| `out/icon.c/` | 5 |
| `out/merge.ladder/` | 5 |
| `out/draw.clone/` | 5 |
| `out/draw.variant/` | 5 |
| `out/icon.b/` | 1 |

明细见同目录 `suite_moves.json` 与完整日志 `classify-watch.txt`。

## 说明

- 本支 **text_only**，未重生图。
- 高置信自动模块名多来自路径/文件名信号（如 `ui.R3`、`ui.merge.ladder`），属 classify-watch 默认行为；未为清空列表强行移动低置信项。
- `merge.ladder/final.jpg` 已入库到 `assets/ui/merge.ladder/final.jpg`；suite 原路径上仍可见同内容文件（归档日志记 `moved=true`）。
- 日志：`classify-watch.txt` · `list.txt` · `atlas.txt`
