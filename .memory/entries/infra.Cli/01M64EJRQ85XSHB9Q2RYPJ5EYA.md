---
id: 01M64EJRQ85XSHB9Q2RYPJ5EYA
module: infra.Cli
entity: StopThresholdDefault
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py
- lifecycle.py
- .memory-art/config.yaml
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: CLI与项目config默认停机线必须是9.5，与DEFAULT_THRESHOLD一致
verify: python3 pmem_art.py converge -h 显示默认 9.5；.memory-art/config.yaml 四档均为 9.5
applies: 本仓库 converge CLI 与项目初始化默认配置
aliases:
- threshold默认
- '9.5'
- 停机线CLI
source:
  conversation: 3551449c-c43f-4703-8575-43749b09f5ba
---
需求来源：用户 2026-10-30 把 converge 停机线从 9.6 改为 9.5；
CLI、lifecycle 写入的项目 config、用户手册里的默认值必须跟 skills_kit 合同一致，否则 `converge start` 不传 --threshold 时仍按旧线停。
必须保持：`python3 pmem_art.py converge` 的 `--threshold` 默认 9.5；
lifecycle / 项目 `.memory-art/config.yaml`（含子项目）的 `converge.target_thresholds` 四档均为 9.5；
USER_MANUAL / AGENTS 等入口文档写合格线 ≥9.5。
历史会话 JSON 不回溯改写。
入口：pmem_art.py converge 参数；lifecycle 默认 target_thresholds；.memory-art/config.yaml。
