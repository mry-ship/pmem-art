---
id: 01M8C5594BN0GMZ5Q5JF4VNRM8
module: feature.SkillsKit.Draw
entity: SplitLensTouchup
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_registry.py#build_registry
- skills_kit/skill_specs.py
- skills_kit/agent_router.py#plan_route
- skills_kit/route_gate.py
revision: git:d08caf0
author: 1002378395@qq.com
note_date: '2026-11-26'
summary: 镜头包与局部改拆为 /pmem-lens、/pmem-touchup，路由 id 不变
verify: pytest tests/test_skill_router.py；build_registry(SKILL_SPECS) 的 section_cut_ok
  为 True
source:
  kind: code
---
镜头包(draw.lens)和局部改(draw.touchup)从 pmem-draw 拆成独立技能 /pmem-lens、/pmem-touchup。
正文放 skills_kit/data/pmem_lens_skill_body.md 与 pmem_touchup_skill_body.md，由 SKILL_SPECS 加载。
注册表 _DRAW_HEADING 把两个 id 映射到新技能，执行包只含「零点五 route + 合同」，不带闭环、交件可见、记忆静默。
agent_router 点名映射、route_gate._SLASH_TO_ROUTE、art_doctor_ext 清单、modules.yaml(Lens/Touchup 模块)同步。
pmem-draw 里两节已删，认成表改为转交。
注意 skill_specs.py 与 data/*.md 全是 CRLF，改写须保持 CRLF。
