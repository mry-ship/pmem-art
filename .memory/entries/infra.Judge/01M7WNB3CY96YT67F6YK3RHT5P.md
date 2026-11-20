---
id: 01M7WNB3CY96YT67F6YK3RHT5P
module: infra.Judge
entity: ScoringCanon
kind: feature
status: active
supersedes: []
anchors:
- docs/SCORING_CANON.md
- vlm_judge.py#build_judge_system_prompt
- ARCHITECTURE.md
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 正式尺六维；Absolute-5D是工艺五维别名
verify: docs/SCORING_CANON.md 存在；ARCHITECTURE 4.1 写六维真源
applies: 改评分文案、Judge提示或停机规则时
aliases:
- Absolute-5D
- 六维
- 无瑕度
- SCORING_CANON
source:
  conversation: c8eef2a3-73d7-46b8-850d-eeac1e85ee27
---
需求来源：README六维、架构Absolute-5D、vlm_judge五维+无瑕度表述漂移。
必须保持：
- 对外正式呈现与停机按六维加权调和平均（无瑕度约25%）；
- Absolute-5D / parse_5d_dims 为工艺五维历史名，有flawlessness时按六维；
- 真源 docs/SCORING_CANON.md；ARCHITECTURE/USER_MANUAL/RULES 交叉引用，禁止再分叉一套尺。
auto_validate_on_save 仍为保留字段、CLI未读（质检非落盘阻断）——与架构一致，勿谎称已硬闸。
