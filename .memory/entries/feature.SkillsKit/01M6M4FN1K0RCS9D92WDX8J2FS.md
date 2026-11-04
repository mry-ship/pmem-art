---
id: 01M6M4FN1K0RCS9D92WDX8J2FS
module: feature.SkillsKit
entity: SkillSpecAudit20261105
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py
- skills_kit/converge_policy.py
- skills_kit/converge_loop.py
- skills_kit/install.py
- skills_kit/skill_registry.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: UI范例降级、软糖条件化、merge矛盾修复、路由冲突闸、三透镜齐
verify: rg 路由冲突闸|非糖果且未点名|仅当题材是软糖|MERGE_MULTI_LENS；pytest tests/test_skill_router.py
  tests/test_merge_relation.py -q
applies: 改 /pmem-* 技能文案或 install 后
source:
  conversation: ccfc4c53-773f-4c77-90b0-4088c1330449
---
用户2026-11-05要求按审计清单修正技能。
已改 skill_specs 并 skills --install：
1) UI：通用落位+多维透镜与 RM 三消范例拆分；主 CTA 跟对标真图不锁死巨 PLAY。
2) Draw：软糖 SSS 仅软糖题材强制。
3) Merge：禁止条改为「非糖果未点名禁默锁 shop_ladder」；补 docs/MERGE_MULTI_LENS.md。
4) Agent：execute_ok 仍可被路由冲突闸打成 ask。
5) Icon B/C 短透镜；Critique 分尺说明；Prompt 挂 UI/APPICON/MERGE 透镜。
6) recompose 主光句改为通用来源，例句非二选一。
相关 docs：UI_MULTI_LENS / APPICON_MULTI_LENS / MERGE_MULTI_LENS。
