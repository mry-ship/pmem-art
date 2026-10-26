---
name: pmem-atlas
description: 当用户输入 /pmem-atlas 或 /art-map 时触发。自动扫描归位未分类散图、运行管线与记忆过期体检，并重新生成 art-atlas.html。
---

# `/pmem-atlas`（别名 `/art-map`）— 整理散图与刷新可视化图谱

当用户想阶段性整理项目里的生成图、查看目前积累了多少条红线与定稿配方时执行：

1. **扫描未归档新图**：
   ```bash
   python3 pmem_art.py classify-watch
   ```
   汇报有哪些散图待归档（若用户同意，加 `--apply` 自动归位）。
2. **模块与记忆总览**：
   ```bash
   python3 pmem_art.py list
   ```
3. **重新编译单文件交互式图谱**：
   ```bash
   python3 pmem_art.py atlas
   ```
   告知用户可随时双击项目根目录的 `art-atlas.html` 检视正反例滑杆与配方卡。
