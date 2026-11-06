---
id: 01M6RABZHFXV320X355C412DZD
module: feature.SkillsKit
entity: RouteGateAndRegistryFixes
kind: correction
status: active
supersedes:
- 01M6R96HGAYHQ6E6Q8PM7WHY5F
- 01M6R7WZF85NZNMGCQD527RW4Y
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
- skills_kit/agent_router.py#_ascii_word_hit
- skills_kit/skill_registry.py#build_registry
- skills_kit/skill_registry.py#write_registry_files
- skills_kit/merge_relation.py#split_sheet_grid
- skills_kit/converge.py#_split_speed_requested
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: _dev_ops_ask 改边界匹配;registry file 按平台前缀;split_sheet 单居中;cap 认 draw.multi
verify: plan_route('clip the character').route_ids==['draw.ordinary'];plan_route('流程图有没有
  bug').reason=='unrecognized';三平台 registry.json routes[].file 从仓库根 os.path.exists
  均真;_split_speed_requested(route_ids=['draw.multi'])是 True;unittest tests.test_route_false_fire
  通过
applies: 改 _dev_ops_ask 词表/匹配、registry file 前缀、split_sheet_grid 或 split 限轮判定时
aliases:
- 子串误杀
- cli吃clip
- 图吃试图
- registry file 仓库根
- split_sheet 双居中
- draw.split draw.multi 命名
---
复审四处修复（都在本工作树成立，与主目录未提交改动无关）：
1) _dev_ops_ask 子串误杀：原按子串匹配，cli∈clip 误杀、图∈试图/流程图 和 ui∈requirements 把闸关掉。
   改：ASCII token（bug/hooks/pytest/cli/skill/registry/agent_router/converge/review/changes）走 _ascii_word_hit 单词边界 (?<![a-z])w(?![a-z])；
   CJK 禁单字，去掉裸 图/画，美术对象改用 画一张/画个/构图/图标 等整词。
   _DEV_OPS_ASCII/_DEV_OPS_CJK/_ART_OBJ_ASCII/_ART_OBJ_CJK 四表。
   补了 哪里不对/review recent changes。
2) registry file 路径：上次改成平台中性 skills/<n>/SKILL.md，从仓库根读不到（实际在 .cursor/.claude/.agents 下）。
   改：build_registry 加 platform_dir 参数打前缀，_icon_routes 接 icon_file；
   write_registry_files 按三平台各 build 一次，每份 registry.json 带本平台前缀，从仓库根直接可读；
   运行时默认 .claude。
   三份 registry.json 的 file 字段现在按平台不同（故意），SKILL.md 正文仍三平台一致。
3) split_sheet_grid 双调用 cell_to_equal_square：该函数按主体占比重放，二次调用会把已居中方图再检测再缩放、挪动构图。改成只居中一次保存。
4) _split_speed_requested 的 ids 判断原只认 draw.split（路由从不产出），实际路由写 draw.multi、靠 --contract split/关键词兜底。
   补上 draw.multi，漏标志位也限轮。
全量 416 项里 8 个失败（doctor/param/warm-start/coach/打包）经 clean-HEAD 回跑确认 pre-existing，非本次引入。
