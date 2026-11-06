---
id: 01M6RD0FRM0MM0MG2ZCXNHSFAV
module: feature.SkillsKit
entity: DevOpsTalkGate
kind: correction
status: active
supersedes:
- 01M6RCN8T8R2Q30S10ZZERAWVC
- 01M6R7Q2FCV3C4K44SZNKGX9ZH
anchors:
- skills_kit/agent_router.py#_non_art_ops
- skills_kit/agent_router.py#plan_route
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 主目录窄闸仍把查bug口语送进普通图；工作树闸不完整
verify: pyw -3 -u -c "from skills_kit.agent_router import plan_route; print(plan_route('详细检查是否哪里有漏洞bug').route_ids)"
applies: 总控路由把主目录与 quizzical-hugle 工作树的 agent_router 合成之前
aliases:
- 查bug
- 漏洞
- 误开画
- bugs复数
- 裸图标
source:
  conversation: 2fb9d6ff-529d-4817-aa0f-d09fd39d062b
---
实测主工作区 skills_kit/agent_router.py 的 _non_art_ops 只拦「检查技能 / 单元测试 / 修 converge|bug」这类短句。
「你再深度检查下整个项目是否还有什么漏洞bug」「详细检查是否哪里有漏洞bug」「帮我看看有没有 bug」「审计一下 hooks」都走 plan.reason=default、route=draw.ordinary。
.claude/worktrees/quizzical-hugle-e0a15e 的 _dev_ops_ask 能停住上面这些句，但单词边界把 bugs 复数和 hook 单数放跑（「有没有 bugs」「fix the bugs」「审计一下 hook」仍是普通图）；
没有代码锚点的「深度检查整个项目」「review the code」也落普通图。
同一句「对比页把图标和合成梯都再跑一遍」：主目录停在 icon_unspecified；
工作树没有 _showcase_bare_icon，只出 merge.ladder 并执行。
「都按这张画一张窗边女孩」主目录是 style.lock→draw.clone，工作树掉成普通图。
两边都是同一提交 0e08123 上的未提交改动，HEAD 里这三个符号都不在，不能只合一边。
