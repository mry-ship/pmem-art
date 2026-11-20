---
id: 01M7X9MZG339X932WPG5H6NQJZ
module: feature.SkillsKit.Registry
entity: GridPackVisible
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py#_DELIVERY_VISIBLE
- skills_kit/data/pmem_layer_split_skill_body.md
revision: git:ea22106
author: yanghu
note_date: '2026-11-21'
summary: 四格与防污染写入执行卡和交件可见
verify: pytest tests/test_skill_router.py -q；slice 含四格不进路由句；layer.split 不含统一CLI；pack_line≤120
applies: 总控按 pack_headings 把执行包交给执行侧时
---
需求来源：防污染规则只写在完整技能正文或规划里时，执行包切片读不到。
必须保持：四格合同和防污染写在已打包的「执行卡」与「交件可见」内，不新开一级标题，不改变两节结构。
layer.split 仍只装执行卡+交件可见，禁止整份 H1。
界面、图标、合成梯、普通图/克隆同样能在执行包里读到「四格不进路由句」。
未点名接续垫图目录不放宽。
双参考像素同框仍硬停。
轮次上限仍是 3。
适用条件：改技能结算或执行卡文案时，必须改会被 slice_route_body 带走的节。
入口：contract set --keep --vary --forbid --spec；标准路由句不接收四格。
