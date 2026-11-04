---
id: 01M6KVQMRB1SPADW8616QRQYJV
module: feature.SkillsKit
entity: MergeChainMode
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#judge_relation_rows
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: same_object 禁礼盒奖杯换货主语；英文 base_body 可对中文母体词
verify: python3 -m pytest tests/test_merge_relation.py::MergeRelationTests::test_same_object_rejects_gift_box_subject_swap
  tests/test_merge_relation.py::MergeRelationTests::test_en_base_body_matches_zh_silhouette
  -q
applies: pmem-merge-ladder 关系稿 judge_relation_rows
aliases:
- same_object
- 换货
- 礼盒
- base_body
---
现象：电池 phase1 把 L5–L8 写成礼盒/奖杯主体，关系稿表面过关但成图必然 shop_ladder 化。
根因：same_object 只查空零件/体量，未拦换货容器主语；
英文 base_body=strawberry soft candy 对中文「草莓软糖」零命中。
结论：chain_mode=same_object 时剪影/名称不得以礼盒|奖杯|宝石|宝箱|糖罐等起头，parts_add 不得是独立换货主体；
base_body 用 EN↔CJK 同义匹配。
要换货须显式 shop_ladder。
