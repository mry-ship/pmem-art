---
id: 01M7WNB2RCGZAMPDNB7343VX58
module: feature.Improve
entity: MemoryTrust
kind: feature
status: archived
supersedes: []
anchors:
- improve/memory_trust.py
- feedback.py#write_memory_entry
- improve/warm_start.py#build_warm_start_pack
- skills_kit/converge.py
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 二次过线自动升verified；candidate堆积进doctor
verify: unittest tests.test_memory_trust tests.test_art_doctor_ext -q
applies: converge finish 写记忆后；doctor 巡检时
aliases:
- 二次过线
- auto:repeat_pass
superseded_by: 01M80TRUSTFIXNOAUTOVERIFY
---
需求来源：继续落地记忆晋升。
必须保持：同模块≥2条显式score≥9.5的live recipe时，finish后maybe_auto_verify_on_repeat_pass把candidate升verified（by=auto:repeat_pass），不升canonical；
doctor统计candidate堆积并给修复建议。
入口：improve/memory_trust.py；
lifecycle collect_doctor_summary。
（2026-11-23：自动升 verified 已废，见 01M80TRUSTFIXNOAUTOVERIFY；candidate 堆积仍成立。）
