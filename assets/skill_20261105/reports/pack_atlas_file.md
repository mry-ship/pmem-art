# EXEC PACK atlas.file

banner heading: # `/pmem-atlas` — 整理散图与刷新可视化图谱
skill: pmem-atlas

# `/pmem-atlas` — 整理散图与刷新可视化图谱

当用户想阶段性整理项目里的生成图、查看目前积累了多少条红线与定稿配方时执行：

1. **扫描未归档新图**：
   ```bash
   python3 pmem_art.py classify-watch
   ```
   汇报有哪些散图待归档。**无散图 / 空结果**：说「没有待归档散图」，跳过归位，不要装作扫到了文件。若用户同意归位，先复述将移动的路径，再加 `--apply`（**禁止**静默 `--apply`）。
2. **模块与记忆总览**：
   ```bash
   python3 pmem_art.py list
   ```
3. **重新编译单文件交互式图谱**：
   ```bash
   python3 pmem_art.py atlas
   ```
   告知用户用终端打印的 **`http://127.0.0.1:<端口>/art-atlas.html`** 打开工作台（或双击根目录「打开工作台.cmd」）。**禁止**只双击磁盘上的 `art-atlas.html`：`file://` 下删除/文件夹定位常被浏览器拦住。

**失败话术**：端口占用 → 换端口或关掉旧 atlas 进程后再开，把新 URL 给玩家；命令非 0 → 贴最后几行 stderr，不要假装图谱已刷新。