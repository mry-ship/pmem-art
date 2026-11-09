---
id: 01M6R96HGAYHQ6E6Q8PM7WHY5F
module: feature.SkillsKit.Router
entity: DevOpsTalkGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
- skills_kit/agent_router.py#plan_route
- tests/test_route_false_fire.py
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 研发/排查口语(无美术对象词)走 stop/unrecognized,不兜底普通图
verify: plan_route('帮我看看有没有 bug').reason=='unrecognized' 且 route_ids==[]；plan_route('画一张赛博朋克城市').route_ids==['draw.ordinary']；plan_route('审一下这张图哪里不合理').route_ids==['critique.review']；unittest
  tests.test_route_false_fire 通过
applies: 改 agent_router 兜底判定、_DEV_OPS_OBJ/_ART_OBJ 词表或 _dev_ops_ask 时
aliases:
- 研发口语路由
- 查bug误开画
- _dev_ops_ask
- 排查口语兑底普通图
---
需求：纯研发/排查口语（查 bug、审代码、跑测试、看仓库——「帮我看看有没有 bug」「审计一下 hooks」「看看 agent_router 有没有坑」「详细检查是否哪里有漏洞bug」）此前 default→draw.ordinary 兜底，会让总控误开画。
修法：agent_router 新增 _dev_ops_ask(text)——句内命中代码域对象词 _DEV_OPS_OBJ（bug/漏洞/hooks/单元测试/converge/注册表/代码/脚本/技能/路由/skill/registry/agent_router/cli/重构…）且不含任一美术对象词 _ART_OBJ（图/立绘/画/构图/光影/色板/这张/图标/界面/合成梯…）时为真。
plan_route 在 _named_skill 解析后、仅当 not named 时判 _dev_ops_ask → _stop('unrecognized','这像是查代码/排查，不是出图需求…')。
必须保持：点名 /pmem-skill 的不进此闸；
带美术对象词的审图/出图不被误杀（「审一下这张图」→critique.review，「画一张赛博朋克城市」→draw.ordinary，「用这个技能画一张猫」因含画/猫仍 draw.ordinary）。
背景：这是用户三条审计里唯一在本 worktree 复现的真问题；另两条（都按这张→锁风格串克隆、draw.multi 双 append）经实测不成立/是故意设计，未改。用户点名的 _non_art_ops 在本仓库不存在。
