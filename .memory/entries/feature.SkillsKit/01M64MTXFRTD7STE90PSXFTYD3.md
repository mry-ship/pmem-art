---
id: 01M64MTXFRTD7STE90PSXFTYD3
module: feature.SkillsKit
entity: ShowcaseRerun
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_showcase_ids
- skills_kit/converge.py
- skills_kit/skill_specs.py
- tests/test_showcase_route.py
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 同范围全部重跑默认全清单；展陈路径不被 assets 覆盖
verify: python3 -m unittest tests.test_showcase_route tests.test_showcase_gate -q；pmem_art.py
  route --text "全部重跑 homepage" --canonical "整页展陈同范围重跑"；showcase-gate --html docs/showcase/homepage_rerun_1028_regen3/index.html
applies: /pmem-agent 展陈同范围重跑与 converge finish/status
source:
  conversation: ad2110dc-14c1-4866-a441-1909136ea8d1
---
需求来源：玩家指着 homepage_rerun 说全部重跑并要求反向修技能。必须保持：
  1) 路由 _SHOWCASE 认全部重跑/再跑一遍/同范围；
探针含克隆/变体/锁风格/提示词；
未点名单支时用 _SHOWCASE_DEFAULT_FULL 九支清单可执行；
对比页没写支仍 showcase_unspecified。
  2) converge status 未满4轮且<9.5 时措辞为预览须继续，不得像已终稿。
  3) finish 对 docs/showcase/ 胜出图只写 asset_image 副本，不覆盖 winner.image。
  4) 变体表情差分须可量测部位硬验收。
入口：skills_kit/agent_router.py、converge.py、skill_specs 变体合同；
测试 tests/test_showcase_route.py。
