---
id: 01M642X4H1C0ZVG4B4N8EBYF5W
module: infra.Scripts
entity: NotContract
kind: exclusion
status: seed
supersedes: []
anchors:
- scripts/pack_pmem_art.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 批跑脚本不是skill合同，合同只在skills_kit
verify: 合同改动落在 skills_kit 而不是 scripts 里复制一份提示词
applies: 改闭环、展陈闸门、合成梯规则时
aliases:
- 批处理
- 重跑脚本
verified: '2026-10-30'
verified_at: '2026-10-30T01:52:48.704+08:00'
---
依据模块划分和 scripts 目录用途。
scripts/ 与 benchmark_evolution.py 是展陈重跑、批处理，不是 skill 合同真值。
排除：改停机规则、垫图、合成梯合同时去改批跑脚本而不改 skills_kit。
脚本可以调用闸门，但合同以 skill_specs / converge_loop 为准。
