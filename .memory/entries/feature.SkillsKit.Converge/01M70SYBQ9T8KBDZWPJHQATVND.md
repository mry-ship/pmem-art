---
id: 01M70SYBQ9T8KBDZWPJHQATVND
module: feature.SkillsKit.Converge
entity: FinishSettleBackground
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_spawn_detached_finish_settle
- skills_kit/converge.py#_cmd_converge_settle
- pmem_art.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: finish 默认后台 settle，不挡用户返回
verify: python3 -m pytest tests/test_process_board.py::TestProcessBoard::test_finish_background_settle_does_not_block
  -q
applies: converge finish 结算时
---
画师反馈 finish 收尾卡住对话。
改动：CLI converge finish 默认 settle_background=True，detach 子进程跑 converge settle（写 recipe/红线/反思/autopilot + atlas）；
finish 同步只做胜出结算、final 槽、过程板、报告。
API converge_finish 默认仍同步（测例断言）。
--settle-sync 或 PMEM_FINISH_SETTLE_BG=0 可强制同步。
