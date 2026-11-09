---
id: 01M6RBYBH4NERC9BGF07BVFC1G
module: feature.SkillsKit.Router
entity: DevOpsTalkGate
kind: correction
status: active
supersedes:
- 01M6RACZZA1SH1XXP7EVC27EBC
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 弱词误停已收，技能词被删且单测/用例仍子串误伤
verify: plan_route('检查技能是否有问题').reason=='unrecognized'；plan_route('简单测试一下这个姿势').reason!='unrecognized'；plan_route('检查角色代码有没有
  bug').reason=='unrecognized'
applies: 改 _DEV_OPS_CJK / _ART_OBJ_CJK 时
---
review/changes/哪里不对/接口/重构 的误停已收，review the lighting、脸哪里不对、接口处金属接缝会放行。新问题：
  1) 删掉「技能」后，检查技能是否有问题、审计一下技能文档又落回普通图。
  2) 「单测」是「简单测试」的子串，「用例」是「使用例子」的子串，简单测试一下这个姿势、使用例子说明一下会被停成查代码。
  3) 美术放行词含角色/比例/颜色，检查角色代码有没有 bug、看看报错比例会被放行成普通图。
bug/hooks 也会停掉 draw a cute bug、fish hooks。
切格一次居中和 draw.multi 硬顶仍在。
主目录未提交的都按这张画一张误进锁风格未动。
