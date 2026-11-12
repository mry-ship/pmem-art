---
id: 01M77SY0124JKRF8P4AVYH8FDW
module: feature.SkillsKit.Router
entity: DevOpsTalkGate
kind: correction
status: active
supersedes:
- 01M6RDK6FHP9W0P2JDC0J22WKS
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
- skills_kit/agent_router.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: DevOps闸覆盖项目中/管线/提示词方向审计口语
verify: unittest tests.test_route_false_fire.RouteFalseFireTests.test_non_art_ops_stop_not_ordinary；plan_route(检查一遍项目中…提示词方向)
  mode=stop reason=unrecognized
applies: 总控 route 遇到查项目/管线/提示词方向漂移的研发审计口语时
aliases:
- 提示词方向
- 项目中检查
- 管线审计
source:
  conversation: b184581b-9d2c-4d9d-9f09-b09811f9f431
---
现象：口语「检查一遍项目中是否有哪些环节…提示词方向变化」未命中「整个项目/仓库/代码库」，plan_route 误收成普通图。
更正：_DEV_OPS_PHRASE 增加「检查…项目中/里/内/是否/有哪些/管线」「检查…管线/环节/漂移/提示词方向」与「提示词/brief…方向/漂移…问题」；
_DEV_OPS_CJK 补「提示词方向/方向漂移」。
仍靠三层判定，画一张/审光影放行。
与旧 DevOpsTalkGate 互补，不推翻三层锚点逻辑。
