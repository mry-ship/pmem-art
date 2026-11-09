---
id: 01M6RCAPCVGZ0P7E3NXH0SCPXW
module: feature.SkillsKit.Router
entity: DevOpsGateThreeLayer
kind: correction
status: active
supersedes:
- 01M6RBM6MV3QZSW1A0XKJE34F3
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
- tests/test_route_false_fire.py
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: _dev_ops_ask 改三层判定:强锚点+美术名词守卫+硬词压软词
verify: plan_route('draw a cute bug')/('a pile of fish hooks')/('画一只 bug 怪物')/('简单测试一下这个姿势')/('使用例子说明一下')
  都不是 unrecognized；plan_route('检查技能是否有问题')/('检查角色代码有没有 bug')/('看看报错比例') 是 unrecognized；unittest
  tests.test_route_false_fire 通过
applies: 改 _dev_ops_ask 判定逻辑或 _DEV_OPS_*/_ART_* 词表时
aliases:
- draw a bug 误杀
- 单测用例子串
- 角色比例压代码词
- 研发口语闸三层
verified: '2026-11-10'
verified_at: '2026-11-10T02:23:39.834+08:00'
---
_dev_ops_ask 第三轮重写：放弃「锚点词 + 任一美术词即放行」的两层逻辑（关键词分不开 draw a bug / fix a bug），改三层：
1) 必须命中强代码锚点 _DEV_OPS_ASCII(bug/hooks/pytest/cli/skill/registry/agent_router/converge)或 _DEV_OPS_CJK(漏洞/单元测试/注册表/代码/脚本/函数/报错/堆栈/技能/路由/闸门/实现是否有问题 等整句)；
   无锚点放行。
2) 美术主体名词框 _ART_NOUN_GUARD（draw(ing) a/an、a cute|pile|bunch of、画一只/个/张/群/条/头）命中 → 判美术（draw a cute bug、a pile of fish hooks、画一只 bug 怪物 不被停）。
3) 软美术词（角色/比例/颜色/金属/接缝/特写/脸 等）单独出现判美术；
   但硬代码词 _DEV_OPS_HARD（bug/hooks/pytest/skill/registry/agent_router/converge/cli/漏洞/单元测试/注册表/代码/报错/脚本/函数/堆栈）出现则压过软词，仍判查代码（检查角色代码有没有 bug、看看报错比例 → stop）。
修了本轮三处：技能放回代码词（画一张仍放行）；删 单测/用例（子串咬 简单测试/使用例子）；bug/hooks 整词不再误杀 draw a cute bug / a pile of fish hooks。
ASCII 仍走单词边界。取舍不变：review recent changes 走普通图不 stop。
