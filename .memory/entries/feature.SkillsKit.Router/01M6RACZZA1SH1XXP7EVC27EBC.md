---
id: 01M6RACZZA1SH1XXP7EVC27EBC
module: feature.SkillsKit.Router
entity: DevOpsTalkGate
kind: risk
status: active
supersedes:
- 01M6R9FQ13BFXYKHN4SJXN8NNW
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: review/changes/哪里不对 会把美术句停成查代码
verify: plan_route('the light changes at dusk').route_ids==['draw.ordinary']；plan_route('review
  the lighting').reason 不是 unrecognized
applies: 改 _DEV_OPS_ASCII / _DEV_OPS_CJK 时
---
子串误杀已收：cli 不再吃 clip，单字图不再放行试图/流程图。
新问题是词太碎：review、changes 各自成词，the light changes at dusk、review the lighting、review this key art 被停成 unrecognized。
哪里不对会停掉脸哪里不对、颜色哪里不对；
接口、重构会停掉接口处的金属接缝、重构角色比例。
应绑成短语，不要拆成单词。
切格二次居中和 draw.multi 硬顶在 quizzical-hugle 已修好。
主目录未提交的都按这张画一张误进锁风格仍未动。
