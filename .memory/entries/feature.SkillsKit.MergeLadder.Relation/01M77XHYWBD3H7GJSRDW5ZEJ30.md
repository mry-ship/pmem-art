---
id: 01M77XHYWBD3H7GJSRDW5ZEJ30
module: feature.SkillsKit.MergeLadder.Relation
entity: MergePhotoInventoryGate
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#judge_relation_rows
- skills_kit/merge_relation.py#photo_microdetail_hits
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 档位句禁美食摄影质感词，否则盖过糖釉不是实物
verify: py -3 -m unittest tests.test_merge_relation.MergeRelationTests.test_photo_microdetail_in_silhouette_blocked
  -v
applies: 休闲 merge 关系稿与出图；玩家未点名写实/摄影时
aliases:
- 焦斑
- 柠檬片
- 档位写实
- 美食菜单盖过surface
source:
  conversation: fda824e5-6393-4f0c-859e-6a0bf93b50bd
---
现象：海鲜 merge 首轮无垫图，surface 已禁写实，成图仍偏美食写实。
根因：phase1/prompt 的 L 档写了「焦斑/柠檬片/汤面感/分区摆放」等摄影质感词，与「不是实物」同句并存，引擎优先执行菜单细节。
排除：未点名写实时，silhouette/name/parts_add/merge_why 禁止焦斑烤痕鳞片微距湿润汤面感柠檬片香菜末分区摆放摄影级摆盘等词；
只写糖釉玩具剪影/件数/容器/完成态与整块色。
点名写实或 allow_photo_detail=true 才放行。
