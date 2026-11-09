---
id: 01M6JW8CH2W2HYZ5SB062D3ZV5
module: feature.SkillsKit.Converge
entity: MergeLadder
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- tests/test_skill_router.py
revision: git:7f67ea9
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 合成梯技能合同短语回写并过测
verify: python -m pytest tests/test_skill_router.py::SkillRouterTests::test_router_safety_gates_stay_in_the_contract
  -q
applies: 改 pmem-merge-ladder 文案或 skill_specs 时
---
需求来源：体检全量测试失败，合成梯 SKILL 改写后丢掉合同锁句。
必须保持：固定 3 稿不再拉到 8 稿；
合成说不通仍不算定稿；
画风已写成一句；
不要把参考图文件垫进生图；
同框不是交货；
每一档单独出一张正方形；
六条都要过；
L8≤0.80；
canonical track 不改；
normalize 后再跑一次 audit。
适用：/pmem-merge-ladder。
入口：skills_kit/skill_specs.py → skills --install。
