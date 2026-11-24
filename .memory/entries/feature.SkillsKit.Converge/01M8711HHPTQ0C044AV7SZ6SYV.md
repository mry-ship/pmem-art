---
id: 01M8711HHPTQ0C044AV7SZ6SYV
module: feature.SkillsKit.Converge
entity: SlotReserveAndPrepareAbort
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/parallel_slots.py#reserve_slot
- skills_kit/parallel_slots.py#release_slot
- skills_kit/converge.py#abort_prepare_session
- skills_kit/converge.py#cmd_converge_prepare
revision: git:ff5f930
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 启动前按令牌预占槽位；prepare 失败只回滚本次会话
verify: py -3 -u -m unittest tests.test_parallel_reserve tests.test_hard_pits_gates.TestParallelSlots
  tests.test_session_revision tests.test_route_false_fire tests.test_converge_guards.TestPolicyDefaults
applies: converge start / prepare 跨进程抢最后一个并行槽；同一会话号可能被再次启动
aliases:
- 并行槽竞争
- 槽位预占
- prepare 孤儿会话
- prepare_aborted
- slot_token
source:
  conversation: 7f9cd1bd-0998-40af-b6c9-8c432eb321b3
---
需求来源：两个进程同时读活跃会话会同时判定还剩一个槽并同时启动；
prepare 在 start 成功后若合同、合理性或第一轮 emit-prompt 失败，会留下未出图会话占槽。
复查时又发现：失败补偿若按会话号直接删预占，会删掉同号后一次启动的预占，别的任务能钻进最后一个槽。
必须保持：
1. start 先在跨进程锁内写带 token 的预占，再写会话；会话写入成功后只删本次 token。启动失败未写入会话时也只释放本次 token。同一 session_id 重开仍允许。不同 id 抢最后一槽只有一个能预占成功。
2. 预占超过 15 分钟不占槽，判定前清掉。会话本身仍按 slot_stale_hours（默认 36 小时，看文件 mtime），JSON 不因过期而改。
3. 占槽者 = 未终态会话 ∪ 未过期预占（同一 id 不双计）。finished 与 prepare_aborted 不占槽。
4. prepare 预审失败不建会话。
   start 本身失败不把已有会话标成 prepare_aborted。
   合同、合理性、emit-prompt 失败且还没有成图、并且 started_at 仍是本次启动时，才改为 prepare_aborted，写 prepare_failure，追加审计，并只释放本次 slot_token。
   started_at 已变或写入发生修订冲突时不改后一次会话、不删它的预占。
   已有成图则保持原状态并继续占槽。
5. 同一 id 再跑 prepare 用 replace_session 覆盖原文件，不新增第二份会话；审计 jsonl 保留。
入口：converge start（SlotClaim）、converge prepare（失败走 abort_prepare_session）。
