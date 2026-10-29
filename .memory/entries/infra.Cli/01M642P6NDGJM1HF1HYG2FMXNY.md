---
id: 01M642P6NDGJM1HF1HYG2FMXNY
module: infra.Cli
entity: Onboarding
kind: feature
status: active
supersedes:
- 01M642F4Z96F1TGEF11KRZ6N3Z
anchors:
- .memory/modules.yaml
- .cursor/mcp.json
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 开发skill和稳定性必须写入pmem，不能只靠美术记忆
verify: skills_kit 改动后 .memory/entries 有对应 feature/exclusion；.cursor/mcp.json 同时有
  pmem 与 pmem-art
applies: 本仓库开发 pmem-art 期间
aliases:
- 开发记忆
- 接入
---
需求来源：用户加 pmem，是因为美术记忆系统忘得太快，skill、稳定性和跑图会反复重来；
当时只会记美术口味，开发系统本身不记。
必须保持：本仓库已接入 mry-ship/pmem 0.6.1（闸门 block，与 pmem-art Hook/MCP 并存）；
改 skills_kit、闭环、闸门、脚本、测试前查 .memory，改完写 feature/exclusion/risk。
生图口味、recipe、红线仍只进 .memory-art。
不要把开发结论只写进美术记忆。
适用：本仓库开发 pmem-art 期间。
入口：.memory/ 与 pmem MCP；
生图入口仍是 pmem_art.py。
