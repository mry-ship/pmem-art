---
id: 01M74YYJJYX3YW6X7XKYHHE4FC
module: feature.SkillsKit
entity: NoSilentReusePriorDeliverable
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- .cursor/skills/pmem-agent/SKILL.md
- .cursor/skills/pmem-merge-ladder/SKILL.md
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 未点名接续禁止把仓库旧稿旧成图当本趟底稿
scope: project
verify: skills_kit/skill_specs.py 与 .cursor/skills/pmem-agent、pmem-merge-ladder 含「未点名接续
  → 禁止接旧轨」；merge 禁止条含「扫到旧案 ≠ 获准复用」
applies: 所有 /pmem-* 生图与关系稿执行；玩家未点名接续旧稿时
aliases:
- 禁止接旧轨
- 未点名禁止复用旧稿
- 扫到旧案不等于获准复用
verified: '2026-11-11'
verified_at: '2026-11-11T17:52:54.323+08:00'
source:
  conversation: 7f6eb6c5-c94f-491f-9845-6667f9d3d230
---
现象：玩家只说「走 merge 出一组水果」，执行侧 Glob/Grep 扫到 assets 里旧水果 relation/成图后擅自复用，并挂上旧模块名；
随后 Warm-Start 与垫上轮整表把旧坑（半球剖、硬3D写实脸）继承进整轮收敛，越修越像同一张旧图。
排除：玩家未说「接着上次 / 继续这张 / 用这份 yaml·关系稿·目录 / 复用旧成图」时，禁止把旧任务的 relation、phase1、session 成图、同题旧模块名当成本次交付底稿。
扫到 assets/** 旧案 ≠ 获准复用。
允许：只借格式样例（字段怎么写）；题材、档序、surface、模块与输出目录按本句原话新开；Warm-Start 只吸通用教训与红线，不继承旧整表像素身份或旧链档序为本趟选题。
与「本趟玩家已附 ref 且同类任务默认垫同款 ref」区分：那只适用于玩家本趟明确附上的参考，不是仓库旧案自扫复用。
