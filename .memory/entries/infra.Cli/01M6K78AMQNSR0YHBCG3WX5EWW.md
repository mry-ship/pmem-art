---
id: 01M6K78AMQNSR0YHBCG3WX5EWW
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes:
- 01M6GQJ87VKGNQBR16TEFTH111
- 01M6GR2W4C2GFXTWW35XCWEZDQ
- 01M6GR77H579WA7ZSJ0AZ4EK24
- 01M6GYHV97Z8XYDMG0AAWKBNQM
- 01M6H13Y1CBVH7ZVC3V680J615
- 01M6H141PCEHFE8ABAPP6VTBDF
- 01M6JW8BE2JSH46ZE4FJXBC6H1
- 01M6K6K60SYJE89QSPPF8QTS8D
anchors:
- build_atlas.py
- build_atlas.py#openViewer
- build_atlas.py#closeViewer
- atlas_reveal.py#purge_paths_from_atlas_sidecar
- build_atlas.py#syncTrashFilterIntoData
- build_atlas.py#connectOrOfferWorkbenchLauncher
- build_atlas.py#write_workbench_launchers
- build_atlas.py#downloadStartWorkbenchHelper
- atlas_reveal.py#ensure_reveal_daemon
- atlas_index.py
revision: git:8d36bd0
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 工作台：履历/批量删/定位；索引与揭示桥；主画廊只定稿
verify: python pmem_art.py atlas；点文件夹选中文件；删除后刷新不回魂
applies: 使用 art-atlas 工作台时
---
# AtlasWorkbench 合并结论（现行）

## 必须保持
1. 工作台详情展示 converge 提示词履历；批量删除支持勾选/Ctrl+A/Shift；悬停+Delete。
2. 文件夹定位只走 localhost reveal（默认 27865 /api/delete）或下载定位脚本；禁止 window.open(file://目录)。
3. 浏览器不能从 file:// 自动起 Python。正确入口：双击「打开工作台.cmd/.command」、横幅「重试连通」下载启动脚本、或 `python pmem_art.py atlas` 打印的 http。
4. 打开叠层后 400ms 内忽略遮罩误关；✕/Esc 仍强制关。
5. 删除进垃圾桶后必须 purge atlas_data/索引，并按 `_trash/manifest.json` 过滤，刷新才不会回来。
6. 主画廊默认只定稿（可废案）；过程图/参考原图只在放大预览里看。classify_plate 把 rN 过程图与 ref/refs 标成 process/reference；会话 winner 强制 final。
7. 根目录 atlas_index.py / atlas_reveal.py 归属 infra.Cli（与 build_atlas.py 同模块）。

## 排除
- 禁止指望双击 art-atlas.html（file://）由网页 JS 自动启动本机 Python。
- 禁止 reveal 失败时用 window.open(file://文件夹) 当回退。
- 禁止把 converge rN 过程图、垫图参考长期当作主画廊独立卡片。

合并自 8 条 AtlasWorkbench 记忆。
