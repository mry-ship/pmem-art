---
id: 01M6M4SHHSG3NX73GTWW2HXD52
module: feature.SkillsKit.Router
entity: RouteKeywordFalseFire
kind: correction
status: active
supersedes:
- 01M6M2KRHHCFS38HDS2XP431Z5
anchors:
- skills_kit/agent_router.py#plan_route
- skills_kit/agent_router.py#_left_negated
- skills_kit/route_gate.py#check_route_gate
- skills_kit/converge.py#cmd_converge
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 否定不跨句；全清单只在未被否掉的再跑；generate 用当次 route_ids
verify: python3 -m unittest tests.test_route_false_fire tests.test_showcase_route
  tests.test_agent_route_stability -q
applies: 走 route、converge start/generate 时
aliases:
- 误路由
- 全清单
- 开画串台
verified: '2026-11-10'
verified_at: '2026-11-10T02:23:39.834+08:00'
source:
  conversation: bebd9fbe-2671-4d95-aa71-a5515c6fdbf6
---
否定只在同一小句里生效：句号、逗号隔开之后的词不再算被否定。「不要表情差分」「不要做分镜」仍否掉；「不要全部重跑。对比页把界面和合成梯再跑」只留界面和合成梯。整页里没被否掉的「全部重跑/同范围」且没点名单支，仍是九支全清单。
开画：goal 里每一段 4 字以上且不在 route 原文里的汉字都拒绝；
原文最多存 8000 字。
generate 在合理性闸之前，用当次 route 的非空 route_ids 覆盖会话里开局时抄下的列表；
只剩 style.lock 时不能用普通图审核放行。
空 route_ids 仍放行，给旧会话。
