---
id: 01M708NTJM15FT8XQ6X4GHVCX1
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes:
- 01M6NV5WGQ3R50D50GQEQ0G4PC
anchors:
- improve/warm_start.py#entry_on_topic_for_task
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: 暖启补 prop_icon 过滤+水彩卡；早停文案可关
verify: tests.test_warm_start_guardrails；lookup 水彩→watercolor.portrait；窗边水彩 goal 的
  prompt_block 不含 mushroom/红菇/赛璐珞
applies: converge warm-start / benchmark lookup / 技能文案
---
需求：验收出图时 Warm-Start 把 prop icon mushroom recipe 与赛璐珞卡灌进水彩立绘，提示词跑偏；水彩品类 benchmark lookup 找不到卡。
必须保持：已有域过滤与红线封顶仍生效；universal 霓虹/油腻禁令仍注入；prop 任务仍能召回 prop_icon recipe。
入口：improve/warm_start 增 prop_icon/watercolor 主题与知识卡介质冲突过滤；
skills_kit/data/benchmarks/watercolor_portrait.yaml；
skill_specs 安全早停注明 config 可关；
unrecognized 附降级菜单。
旧卡 WarmStartGuardrails 能力保留并扩展。
