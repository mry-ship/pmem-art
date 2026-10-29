---
id: 01M642P5SH0PPGDAMX2YACDRK2
module: infra.Cli
entity: DualMemory
kind: decision
status: active
supersedes:
- 01M642F2X3J3QXTZKHJ1ADV160
anchors:
- .memory/config.yaml
- .cursor/mcp.json
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: pmem用来开发并做稳美术记忆系统，不是再记一遍怎么画画
scope: project
verify: 改 skills_kit 或闭环规则时先 pmem search，结论写 .memory 而不是 .memory-art/recipe
applies: 本仓库仍在开发 pmem-art 的 skill、稳定性和跑图管线期间
aliases:
- 目的
- 主次
- 研发记忆
verified: '2026-10-30'
verified_at: '2026-10-30T01:53:29.919+08:00'
---
用户加 pmem 的原因：美术记忆系统（pmem-art）忘得太快，做技能、稳定性和跑图会反复重来；
当时模块和记忆几乎只覆盖生图口味，开发这个系统本身的结论没有落盘。
pmem（.memory/）的主职责是把 pmem-art 当作正在开发的产品来记：skill 合同、停机规则、闸门、稳定性、展陈重跑里踩过的坑和排除过的方向。
帮 Agent 记住怎么画画、记 recipe/红线，是 pmem-art（.memory-art/）自己的事，不是这次接入 pmem 的目的。
两套仍然不混写，但主次不能写反：先用 pmem 把美术记忆系统做稳，再生图侧的忘记是另一条线。
