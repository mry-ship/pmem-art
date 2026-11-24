---
id: 01M84C0WQGTTBMZ7YQYMXAH6HJ
module: infra.Scripts
entity: LayerSplitSkillSync
kind: conclusion
status: active
supersedes: []
anchors:
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆图层技能不得再写交给叠回 autofit。
verify: 两份技能正文去掉 front matter 后一致，且不含 autofit、略小交给 compose。
source:
  kind: conversation
---
Cursor 技能执行卡曾写「略小、略偏交给 compose」和「大小略漂交给 compose autofit」，和现行合同相反。
现行合同是：位置和跨度跟裁切，画面带一对一贴脚印，scale_mul=1，不 NCC 缩小。
超宽前景不再走 width 模式。
幽灵单层 MAE 标脏不单独重抽。
两份技能正文（skills_kit 与 .cursor/skills）必须一致，闸门数字跟 defaults.py。
