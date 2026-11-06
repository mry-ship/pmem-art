---
id: 01M6R9FQ13BFXYKHN4SJXN8NNW
module: feature.SkillsKit
entity: DevOpsTalkGate
kind: risk
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: _dev_ops_ask 子串匹配会误杀 clip、放行带图的查 bug
verify: plan_route('clip the character').reason 不应是 unrecognized；plan_route('流程图有没有
  bug').reason 应为 unrecognized
applies: 改 _dev_ops_ask / _ART_OBJ / _DEV_OPS_OBJ 时
---
工作树 quizzical-hugle 的新闸用「子串 in 句」。
_ART_OBJ 含单字「图/画」和「ui」，_DEV_OPS_OBJ 含「cli」。
结果：clip the character 因 cli 被停成 unrecognized；
试图修 bug、流程图有没有 bug、requirements 有没有 bug 因句内出现图或 ui 被当成美术句，仍 default→draw.ordinary。
词表应整词或带边界，单字图/画和 ui/cli 不能做子串。
该修只在 .claude/worktrees/quizzical-hugle-e0a15e，主工作区未合入，主工作区未提交的都按这张误路由、切格双次居中、draw.split 硬顶仍在。
