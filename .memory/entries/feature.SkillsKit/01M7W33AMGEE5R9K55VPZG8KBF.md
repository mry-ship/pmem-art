---
id: 01M7W33AMGEE5R9K55VPZG8KBF
module: feature.SkillsKit
entity: DeliveryVisibleElapsed
kind: feature
status: active
supersedes:
- 01M7PPZ0QT7T5JDWNVGRPS23ZG
anchors:
- skills_kit/skill_specs.py#_DELIVERY_VISIBLE
- skills_kit/install.py
- scripts/pmem_layer_split/emit_html.py#_write_layers_click_table
- skills_kit/data/pmem_layer_split_skill_body.md
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 凡交了图必出可点单图表并Read，含拆层/审图/锁风/归档
verify: py -3 -m unittest tests.test_skill_router tests.test_process_board -q；.cursor/skills/pmem-layer-split/SKILL.md
  含「交件可见」；emit 写 assets/*/layers.md
applies: 凡技能结算交了图：闭环轮次/终稿/拆层/审图/锁风样张/归档清单
aliases:
- 可点单图表
- layers.md
- 轮次单图表
- 可点图
source:
  conversation: 8bf3f9f2-0d6e-45db-b55e-017394ead677
---
需求来源：玩家要求每次做完技能都有可点击查看单张图的表（闭环任一轮、终稿、拆层散图等都要）。
必须保持：
1) 出图「## 交件可见」硬规矩：有图就贴 Markdown 可点单图表（相对仓库根链接）+ 对表内每张 Read；闭环另交拼板与本次耗时；judge 后中途也要给本轮可点行。
2) 覆盖 draw/ui/icon/merge；锁风交可点样张表；审图交可点审图表；归档有图则交可点归档表；拆层交 layers.md（emit 写出）并 Read 叠回/幽灵/各层。
3) pmem-layer-split 已纳入 SKILL_SPECS，install 不再 prune 掉；纯文字（提示词/无附图教练）不必出表。
入口：skill_specs._DELIVERY_VISIBLE；install 节3；scripts/pmem_layer_split/emit_html._write_layers_click_table。
