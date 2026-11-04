---
id: 01M6K59CEQC5G3Z9SCZVCP8TKT
module: infra.Cli
entity: AtlasRevealPort
kind: exclusion
status: active
supersedes: []
anchors:
- atlas_reveal.py#ping_server
- atlas_reveal.py#ensure_reveal_daemon
- atlas_index.py#collapse_assets_path_aliases
- build_atlas.py#getFilteredAssets
revision: git:0925f04
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 多项目勿共用27865；资产键须POSIX防双卡
scope: project
verify: 两项目分别 atlas 后 ping 27865/27866 root 不同；Test 画廊无 / 与 \\ 双卡
applies: 本机同时开多个 pmem-art 项目工作台时
aliases:
- 测试项目不显示
- 画廊双份
---
现象：测试项目打开 http://127.0.0.1:27865/art-atlas.html 显示本仓或画廊同一张图双份；进化对照「无闭环会话」。
根因：1) 多项目共用默认端口 27865，ping 不校验 root 会认领别人的守护；2) 记忆条目路径带反斜杠，与扫描 POSIX 键并存，画廊双卡。
排除：继续假定 27865 永远是当前项目；忽略路径分隔符归一。
正确做法：ensure_reveal_daemon/ping 校验 root，被占则换 27866+；资产键一律 POSIX 并 collapse 别名；浏览器 ping 也比对 DATA.root。
