---
id: 01M6RCED9R4HDEB8JWVMNBB70M
module: feature.SkillsKit
entity: DevOpsTalkGate
kind: correction
status: active
supersedes:
- 01M6RBYBH4NERC9BGF07BVFC1G
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 名词框用前缀放行，a little bug 被当成出图
verify: plan_route('a little bug in the renderer').reason=='unrecognized'；plan_route('a
  bug on a leaf').reason!='unrecognized'；plan_route('检查角色路由').reason=='unrecognized'
applies: 改 _ART_NOUN_GUARD / _DEV_OPS_HARD_* 时
---
技能词、单测/用例子串、硬代码词压过角色/比例 都已收。
新闸的美术名词框是前缀正则，不是「bug 当画面主体」。
a little / a bunch / draw a 一命中就放行，所以 a little bug in the renderer、a bunch of bugs in the registry 落成普通图；
draw 左边没有单词边界，withdraw a bug 也会被放行。
框没覆盖的画法仍然停住：a bug on a leaf、paint a shiny bug、sketch a bug、fish hooks on the dock、show her skill。
软美术词会压过未列入硬词的代码锚点：检查角色路由、角色实现是否有问题 被放行；
脚本/函数在硬词里，写个角色脚本 会被停。
主目录未提交的都按这张画一张仍会进锁风格后克隆，这份工作树没有那段改动。
