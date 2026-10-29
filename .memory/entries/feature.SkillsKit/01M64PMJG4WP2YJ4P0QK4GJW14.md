---
id: 01M64PMJG4WP2YJ4P0QK4GJW14
module: feature.SkillsKit
entity: MergeBaseBody
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#judge_relation_rows
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 同物件合成梯可选base_body母体锁；同范围重跑抄死surface
verify: tests.test_merge_relation.MergeRelationTests.test_base_body_locks_mother_mesh；pmem_art.py
  merge relation-judge --all
applies: 同物件合成梯与展陈同范围重跑
aliases:
- base_body
- 母体锁
- merge漂了
source:
  conversation: ad2110dc-14c1-4866-a441-1909136ea8d1
---
需求来源：regen3 药/糖梯与旧展陈视觉相差过大。
必须保持：同物件升档链可在 phase1 yaml 写 base_body；填写后每档 silhouette/name 须保留母体词，否则 relation-judge 失败。换物种链可不写。
同范围重跑必须抄死旧 surface、base_body、零件链；出图句每档重复母体+只加 parts_add。
入口：merge_relation.judge_relation_rows；/pmem-merge-ladder 第一段；regen3 merge_phase1.yaml。
