---
id: 01M64GDM2YA2C37BQ8YWHPHTNW
module: infra.Cli
entity: PmemRuleMarkers
kind: conclusion
status: active
supersedes: []
anchors:
- .cursor/rules/pmem.mdc
- .memory/config.yaml
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 升级pmem后须重跑init刷新mdc，否则缺【pmem】行
scope: project
verify: rg '回复里的【pmem】' .cursor/rules/pmem.mdc 有命中；与 pmem 包 templates.RULE_BODY 一致
applies: 本仓库已装 pmem 且 .cursor/rules/pmem.mdc 由 init 生成时
aliases:
- 【pmem查询】
- 【pmem修改】
- 【pmem检索】
- pmem行不显示
source:
  conversation: f587d48a-52fd-45a6-a9ce-0cd76236e03e
---
现象：询问时看不到【pmem检索】/【pmem查询】，结尾也不见【pmem修改】。
原因：.cursor/rules/pmem.mdc 仍是 2026-10-17 首次接入时的旧模板，缺少「回复里的【pmem】行」整节；
Agent 只按 alwaysApply 规则写回复，Hook 的 stop 催记不等于自动在正文里插这些行。
证据：对照 pmem 0.6.1 的 RULE_BODY（templates.py）含【pmem检索】【pmem查询】【pmem修改】约定；本仓旧 mdc 无此节。
修法：在仓内执行 pmem init --agents cursor，刷新 pmem.mdc（及技能）。config 的 stop_reminder/analysis_reminder 等闸门键保留。
影响：新开对话或规则重载后 Agent 才会按新 mdc 显示；本对话若仍缓存旧规则需新开。
后续：升级 pmem 版本后应再跑一次 init 对齐规则。
