---
id: 01M643G39RRPSTT61Z1NGV1NFT
module: infra.Cli
entity: Packaging
kind: decision
status: active
supersedes: []
anchors:
- lifecycle.py#ensure_cursor_stubs
- skills_kit/install.py#install_skills_and_agent_configs
- skills_kit/skill_specs.py
- .cursor/mcp.json
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 给用户的包只含 pmem-art，不带 mry-ship/pmem 研发记忆
scope: project
verify: python3 pmem_art.py init 写出的 hooks.json 只有 pmem_art.py hook；SKILL_SPECS 只有
  10 条美术技能；pmem_art.py 不 import pmem 包
applies: 给美术用户分发 pmem-art 时；本仓库开发期间仍可同时挂 pmem
aliases:
- 单独打包
- 不带pmem
- 用户包
- standalone
verified: '2026-10-30'
verified_at: '2026-10-30T01:53:09.655+08:00'
---
用户确认：pmem（mry-ship/pmem，目录 .memory/）只为本仓库开发 pmem-art 的稳定性服务；以后给用户的包只打 pmem-art，不带 pmem 研发记忆系统。
两套运行时已经分开：pmem_art.py / .memory-art / 10 条美术技能不 import pmem 包；
init 和 skills --install 只写 pmem-art 的 hook、技能和规则。
本仓库里的 .memory、pmem MCP、pmem hook、pmem.mdc、pmem-bootstrap/seed/spec 等是开发脚手架。
给用户的包必须排除这些，也不能把 pmem 做成 pmem-art 的运行时依赖。
本仓库若直接 clone 给用户，会把 pmem 脚手架一并带走；打包时要另走用户安装路径（init + skills --install）或排除清单。
