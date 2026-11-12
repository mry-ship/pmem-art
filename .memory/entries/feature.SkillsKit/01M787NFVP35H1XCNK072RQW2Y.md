---
id: 01M787NFVP35H1XCNK072RQW2Y
module: feature.SkillsKit
entity: NoSilentReusePriorDeliverable
kind: correction
status: active
supersedes:
- 01M74YYJJYX3YW6X7XKYHHE4FC
anchors:
- skills_kit/prior_reuse_gate.py#assert_no_silent_prior_asset_reuse
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: suite/refs 与 downloads 垫图放行；out/交付仍拦
verify: python -m unittest tests.test_prior_reuse_gate -q
applies: converge start/generate 校验 reference_image_paths 与 goal 内路径时
aliases:
- 接旧轨误伤
- suite refs
- downloads垫图
source:
  conversation: 679ccb52-31d7-4ad3-8b43-02f24338f778
---
现象：全技能清点把 GH 垫图拷到 assets/skill_*_suite/refs/ 或直接垫 downloads/gossip_harbor，开画被「未点名接续」闸误拦。
更正：允许 assets/refs/**、downloads/**、下载/**、assets/skill_*/refs/** 作布局/画风垫图；
仍禁止未点名接续时引用 skill_*/out、sheet_session、phase1、relation.md、.memory-art/converge 板。
不推翻「扫到旧案 ≠ 获准复用」——只把明确参考垫图目录从交付痕迹里摘出。
