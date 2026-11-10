---
id: 01M72JHC4A7KZGNTQ53N4THB4M
module: feature.SkillsKit.MergeLadder.Relation
entity: WaterCartNotCanOnWheels
kind: exclusion
status: active
supersedes: []
anchors:
- assets/skill_20261110_gh_portrait_v2/merge_water/relation.md
- assets/skill_20261110_gh_portrait_v2/merge_water/final.jpg
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 浇水末档禁止壶焊轮架，须一体喷灌车
verify: merge_water final 末格不是独立壶坐在轮架上
applies: 庭院浇水 same_object 合成梯末档
aliases:
- 壶焊轮子
- 浇水壶上轮
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
对照 Merge Mansion Watering 末档是水管+喷头系统一体货。我们浇水 sheet 满4轮9.27分时身份链已对（莲蓬从L4起、L7无喷头卷盘），但L8仍是一把浇水壶焊在四轮架上，且邻档框高阶梯不够导致未过9.5。
排除：末档用「壶+轮」零件拼装冒充升级。
必须：L8罐身即车身、固定喷臂与轮为一体；框高0.40→0.96单调增。
