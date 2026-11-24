---
id: 01M8724MY9DT91SYNDD09HCPBT
module: feature.SkillsKit.Converge
entity: ContractBaseRev
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/understanding_contract.py#save_session_contract
- skills_kit/understanding_contract.py#cmd_contract
- skills_kit/converge.py#_write_session_json
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 保存合同必须带读取时的 base_rev，对不上就拒绝
verify: unittest tests.test_session_revision.SessionRevisionTests.test_stale_contract_does_not_cover_a_newer_contract
  tests.test_session_revision.SessionRevisionTests.test_contract_save_matches_the_rev_from_the_read
  -q
applies: 同一 converge 会话上保存理解合同时
aliases:
- base_rev
- 合同覆盖
- 修订绕过
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：save_session_contract 先重读最新会话，再把调用者手里的旧合同覆盖进去。版本号会加一，但旧合同仍能盖住新合同。
必须保持：save_session_contract 接收调用者读取合同时的 base_rev。
在同一把会话锁里比对磁盘 _rev，不一致就抛 SessionRevisionConflict，不写盘。
写入检查用的也是这个 base_rev，不是刚重读到的修订号。
cmd_contract 的 set / patch 把本次 load 看到的 _rev 传进去。
适用：同一会话上先读合同、后写合同。
入口：skills_kit/understanding_contract.py save_session_contract；pmem_art.py contract set / patch。
