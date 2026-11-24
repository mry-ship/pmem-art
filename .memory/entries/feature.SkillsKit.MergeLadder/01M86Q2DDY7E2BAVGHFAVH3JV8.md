---
id: 01M86Q2DDY7E2BAVGHFAVH3JV8
module: feature.SkillsKit.MergeLadder
entity: MergeSurfacePositive
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#merge_surface_lock_line
- skills_kit/merge_relation.py#photo_microdetail_hits
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 合成梯缺省句只写糖釉玩具货柜，不列禁词
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_merge_without_style_is_gossip_harbor
  tests.test_merge_relation.MergeRelationTests.test_photo_microdetail_in_silhouette_blocked
applies: 合成梯没写风格时灌进缺省表面句；档位字段自己写了摄影质感词时仍打回
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
需求来源：合成梯缺省句把写实摄影、美食棚拍、焦斑、鳞片、湿润一并写进生图提示词，被禁的画面会跟着出现。
必须保持：缺省表面句只写 Gossip Harbor 玩具货柜的正面气质：软立体糖釉、圆润厚实、块面高光、棋盘缩略可认。档位句只写糖釉玩具剪影、件数、容器、完成态和整块色。
档位字段里如果自己写了焦斑、鳞片、湿润、摄影级摆盘，relation-judge 仍打回，文案只说改成糖釉玩具剪影。点名写实或垫真机锁画风仍按原规则放行。
适用：merge 缺省表面与出图模板。
入口：merge_surface_lock_line；/pmem-merge-ladder 出图模板。
