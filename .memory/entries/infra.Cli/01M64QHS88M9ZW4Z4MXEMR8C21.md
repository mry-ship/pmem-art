---
id: 01M64QHS88M9ZW4Z4MXEMR8C21
module: infra.Cli
entity: DocsHomepage
kind: feature
status: active
supersedes: []
anchors:
- README.md
- docs/showcase/skills-homepage/index.html
revision: git:e7ad1e7
author: yanghu
note_date: '2026-10-30'
summary: README含药/糖合成梯L1–L6链路；skills-homepage用1028图源
verify: README 含 merge_potion_l16 与 merge_candy_l16 的 L01–L06；skills-homepage img
  指向 ../homepage_rerun_1028/；含 route_pipeline 链接
applies: GitHub 主页与全页技能展陈
aliases:
- merge链路图
- 合成梯L1-L6
- README合成梯
source:
  conversation: ce0a2f88-0981-43b7-8c37-34c2ca7e87a4
---
需求来源：GitHub 主页 README 效果墙原先只挂了晶冠瓶 T5 单档，没有放合成梯药/糖 L1→L6 链路图；补进 README，并保持 skills-homepage / 手册跳转认路图。
必须保持：README「效果长什么样」内联展示青金治疗药与蜜桃糖各 L1–L6 正方形链路（图源 homepage_rerun_1028/v2/merge_*_l16/）；
T5 晶冠瓶仍可单独出现；
skills-homepage 继续用 homepage_rerun_1028 图与话术样式；
顶栏/手册可点开 docs/route_pipeline.html；
旧 regen2 资产不回链。
入口：README / USER_MANUAL / docs/showcase/skills-homepage/index.html。
