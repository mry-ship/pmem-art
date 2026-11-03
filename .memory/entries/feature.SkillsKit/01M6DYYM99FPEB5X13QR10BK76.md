---
id: 01M6DYYM99FPEB5X13QR10BK76
module: feature.SkillsKit
entity: ReasonablenessGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#check_reasonableness_gate
- skills_kit/converge.py#cmd_converge
- pmem_art.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-02'
summary: 首轮generate前必过合理性闸并强制使用revised提示词
verify: python -m unittest tests.test_reasonableness_gate -v
applies: 跑 /pmem-draw /pmem-ui /pmem-icon /pmem-merge-ladder 或任意 converge generate
  时
---
需求来源：画师反馈多数 skill 出图合理性欠缺，导致迭代久、观感好但最终不通过。
必须保持：
1) 会话内任意一轮 converge generate 前都必须有 passed 的 reasonableness review（禁止用 --round N 跳过）。
2) review 必须同时交 --draft 与更合理的 --revised，并按技能清单 checklist 标 ok。
3) 首轮 generate 强制使用 revised（忽略未再审的其他 --prompt）；非首轮空 --prompt 回退 revised。
4) icon.a 启发式强制安全区+画幅+无字；不过闸则拦截。
不改变 ConvergeGate 的 9.5/满4轮/垫图与 AutoRecall Warm-Start 自动并入。
逃生仅调试：--skip-reasonableness-gate 或 PMEM_ART_SKIP_REASONABLENESS_GATE=1。
入口：skills_kit/reasonableness_gate.py；pmem_art.py reasonableness；skills_kit/converge.py generate 闸；skill_specs 各出图技能。
