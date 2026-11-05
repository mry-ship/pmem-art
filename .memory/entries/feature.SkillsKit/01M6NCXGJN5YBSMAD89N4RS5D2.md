---
id: 01M6NCXGJN5YBSMAD89N4RS5D2
module: feature.SkillsKit
entity: CommercialVibeDefault
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/install.py
- skills_kit/skill_specs.py
revision: git:9d79f57
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 缺风格时按品类抽商业气质，禁一律套软塑胶merge
verify: rg 禁止一律套软塑胶.merge .cursor/rules/pmem-art.mdc；pyw -3 -u -m unittest tests.test_skill_router.SkillRouterTests.test_install_keeps_one_command_per_skill
applies: 玩家未点名画风且无风格参考；普通图/原画/UI/图标A·C/合成梯/提示词/总控可默认
aliases:
- 缺风格商业气质
- 开跑缺风格
---
需求：全修各技能缺风格商业气质，并通检通用性。
必须保持：开跑缺风格写同品类顶级商业气质；
先认品类再抽标尺，禁止一律套软塑胶merge；
UI渲染与布局同对标系且禁默套RM；
图标C按题材品类、有surface则复用；
合成梯因交付是merge才默认休闲货柜；
克隆/变体/图标B不覆盖；
提示词与审图双尺分行；
总控缺风格可默认、品类认不出才硬问。
禁止垫竞品像素。
入口：install.py §6与各SKILL。
