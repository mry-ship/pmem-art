---
id: 01M86SJYFQJXDCB7828YFNJ4S1
module: feature.SkillsKit.Registry
entity: LayerSplitContract
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- skills_kit/data/pmem_layer_split_skill_body.md
- skills_kit/skill_registry.py#_ONE_SECTION
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 拆图层合同钉死位置跨度，禁止当普通图三轮或 autofit 缩小
verify: slice_route_body(layer.split) 含「四格不进路由句」且不含「## 统一 CLI」；unittest tests.test_skill_router
  tests.test_skill_hardening -q
applies: 改拆图层技能正文、描述或 draw 认成表时
aliases:
- 拆图层合同
- autofit
- 位置可漂
---
需求来源：技能文本与路由对不上。
技能描述曾写「大小位置可漂，拼回按脚印 autofit」，与正文「位置和跨度不可漂、scale_mul=1、整幅贴回」相反。
执行包里的四格段还写着「最多 3 轮」，会把拆层引去跑普通图闭环。
必须保持：描述与正文一致，钉死样子、视角、画风、位置和跨度；
叠回按脚印整幅贴回，禁止缩小居中。
总控标准句、生图认成表、提示词类型表都把拆图层单列，转交 pmem-layer-split，禁止在生图技能里 converge start。
拆图层不要写进 draw 的 _DRAW_HEADING，否则会把执行包从「执行卡+交件可见」改成只剩标题。
适用：改技能正文、执行包裁节或拆层描述时。
入口：skills_kit/skill_specs.py 与 data/pmem_layer_split_skill_body.md。
