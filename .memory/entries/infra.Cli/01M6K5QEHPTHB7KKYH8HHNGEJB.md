---
id: 01M6K5QEHPTHB7KKYH8HHNGEJB
module: infra.Cli
entity: AtlasRevealPort
kind: feature
status: active
supersedes: []
anchors:
- atlas_reveal.py#preferred_port_for_root
- atlas_reveal.py#ensure_reveal_daemon
- build_atlas.py#write_workbench_launchers
revision: git:0925f04
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 工作台按项目哈希选端口，占用顺延
verify: python -m unittest tests.test_atlas_reveal_port -q；两项目 preferred 不同且 ping
  root 各异
applies: 安装用户包并打开工作台；本机多项目
---
需求来源：多开项目时 27865 互抢；用户包须工作台稳定可用。
必须保持：
1) preferred_port_for_root 按项目根哈希选 DEFAULT_PORT..+63；ensure_reveal_daemon 占用则顺延，绝不认领他根守护。
2) ping/浏览器探测比对 root；打开工作台.cmd 与定位脚本不写死 27865。
3) 资产键 POSIX + collapse 防画廊双卡；Cursor hooks 含 stop(pyw)。
适用：用户 zip 安装后 atlas / 多项目同机。
入口：atlas_reveal.ensure_reveal_daemon；打开工作台.cmd；pmem_art.py atlas。
