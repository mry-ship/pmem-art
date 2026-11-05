---
id: 01M6NRYPYM02B2W90REWPBM961
module: feature.SkillsKit
entity: MergeOverviewSpeedCaps
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_apply_merge_overview_caps
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: merge整表硬顶3+关系早停+垫上张保质提速
verify: unittest tests.test_merge_overview_caps
applies: delivery=overview_sheet 的 merge.ladder 会话
aliases:
- merge提速
---
需求：用户反馈 merge 出图过慢。
必须保持：出图前五问/机读/商业对标、整表清单验收、默认 overview。
落地：start 识别 merge overview 将 max_rounds 压到 3；
generate 第4次拒跑；
discuss 第4稿拒写；
r2+ 默认垫历史最高分整表；
技能改为关系最多3过了就停、重出≤2条清单、禁套 ordinary 9.5 四轮与商业连刷套。
预期墙钟较翻车路径再少约一半，质量不降闸。
