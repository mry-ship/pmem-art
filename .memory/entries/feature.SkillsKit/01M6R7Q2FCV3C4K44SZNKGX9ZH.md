---
id: 01M6R7Q2FCV3C4K44SZNKGX9ZH
module: feature.SkillsKit
entity: AgentRoute
kind: risk
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_non_art_ops
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: _non_art_ops 漏掉泛化查bug口语会落普通图
verify: plan_route('详细检查是否哪里有漏洞bug').mode=='stop'
applies: 改 _non_art_ops 或默认普通图兜底时
---
新闸只拦检查/审计技能、单元测试、修 converge/路由/bug。
『详细检查是否有漏洞bug』『帮我看看有没有 bug』『审计一下 hooks』仍 default→draw.ordinary。
研发审查句若无明确出图词，应 stop unrecognized，避免误开画。
