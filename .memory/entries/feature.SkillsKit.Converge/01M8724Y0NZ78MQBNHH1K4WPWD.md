---
id: 01M8724Y0NZ78MQBNHH1K4WPWD
module: feature.SkillsKit.Converge
entity: ContractBaseRev
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/understanding_contract.py#save_session_contract
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 保存合同前不能先重读会话再用刚读到的修订号过检查
verify: unittest tests.test_session_revision.SessionRevisionTests.test_stale_contract_does_not_cover_a_newer_contract
  -q
applies: 改合同保存或会话修订检查时
aliases:
- 重读覆盖
- 修订绕过
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
排除：save_session_contract 先把磁盘上的最新 Session 读进来，再把调用者传入的合同对象覆盖上去，然后让 _write_session_json 拿这份刚读到的 _rev 做修订检查。
这样检查会过：A 读到修订 5，B 写成修订 6，A 再保存旧合同时重读到 6，旧合同被写成修订 7。
正确做法是带上读取时的 base_rev，在同一把锁里和磁盘修订比，不一致就拒绝整次写入。
