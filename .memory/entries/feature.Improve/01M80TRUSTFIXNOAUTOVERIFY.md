---
id: 01M80TRUSTFIXNOAUTOVERIFY
module: feature.Improve
entity: MemoryTrust
kind: correction
status: active
supersedes:
- 01M7WNB2RCGZAMPDNB7343VX58
anchors:
- improve/memory_trust.py#normalize_trust
- improve/memory_trust.py#maybe_auto_verify_on_repeat_pass
- improve/memory_trust.py#promote_missing_trust
- improve/warm_start.py#gate_style_memory
- docs/MEMORY_TRUST.md
revision: local:trust-doc-fix
author: cursor-agent
note_date: '2026-11-23'
summary: 自评过线不再自动升 verified；缺 trust 按 candidate
verify: unittest tests.test_memory_trust tests.test_art_doctor_ext -q；docs/MEMORY_TRUST.md
  无「自动升」「祖父条款」
applies: 0.16.16-art 及之后；Warm-Start 注入与 finish 后 trust 晋升
aliases:
- 二次过线自动升
- auto:repeat_pass
- 祖父条款
---
现象：0.16.16 起 maybe_auto_verify_on_repeat_pass 恒返回空；normalize_trust 对缺 trust 的 live 条目改为 candidate；gate_style_memory 只注入 verified/canonical。
更正：verified/canonical 只来自人工 memory promote（及确认过的盲评路径）。旧「二次过线自动升 verified」与「无 trust 按 verified 祖父条款」作废。
落地：docs/MEMORY_TRUST.md 已改；doctor 统计缺 trust；新增 memory audit 与 promote-missing（默认预览，--apply 才写）。
影响：旧库大量无 trust 红线一夜不进提示词，须 audit 后按需 promote-missing。
