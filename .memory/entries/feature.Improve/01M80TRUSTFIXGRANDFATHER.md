---
id: 01M80TRUSTFIXGRANDFATHER
module: feature.Improve
entity: MemoryTrust
kind: correction
status: active
supersedes:
- 01M7WPJV01DX8PQWR422XXR5SA
anchors:
- improve/art_doctor_ext.py#check_candidate_backlog
- improve/art_doctor_ext.py#check_missing_trust
- improve/memory_trust.py#normalize_trust
revision: local:trust-recheck
author: cursor-agent
note_date: '2026-11-23'
summary: 缺 trust 按 candidate；doctor 另计缺 trust 队列
verify: unittest tests.test_art_doctor_ext.TestArtDoctorExt.test_missing_trust_soft_signal
  tests.test_memory_trust.TestNormalizeTrust.test_missing_trust_is_candidate -q
applies: doctor 打印记忆 trust；normalize_trust 缺字段时
aliases:
- 祖父条款
- candidate堆积
---
仍成立：check_candidate_backlog 只计显式 trust=candidate 的 live 条目，provisional 与缺 trust 不进该堆积数。
更正：缺 trust 的旧 active 不再按 verified 祖父；normalize_trust 视为 candidate，且不进提示词。
doctor 用 missing_trust / memory audit 单独统计缺 trust，并用 promote-missing 迁移，不再把「无 trust」说成已验证。
