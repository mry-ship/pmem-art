---
description: 一键归档散图、记忆体检并刷新可视化图谱工作台（pmem-art）
---

# `/pmem-atlas` — 整理散图与刷新可视化图谱

当用户想阶段性整理项目里的生成图、查看目前积累了多少条红线与定稿配方时执行：

1. **扫描未归档新图**：
   ```bash
   pyw -3 -u pmem_art.py classify-watch
   ```
   汇报有哪些散图待归档（若用户同意，加 `--apply` 自动归位）。
2. **模块与记忆总览**：
   ```bash
   pyw -3 -u pmem_art.py list
   ```
3. **重新编译单文件交互式图谱**：
   ```bash
   pyw -3 -u pmem_art.py atlas
   ```
   告知用户用终端打印的 **`http://127.0.0.1:<端口>/art-atlas.html`** 打开工作台（或双击根目录「打开工作台.cmd」）。**禁止**只双击磁盘上的 `art-atlas.html`：`file://` 下删除/文件夹定位常被浏览器拦住。
