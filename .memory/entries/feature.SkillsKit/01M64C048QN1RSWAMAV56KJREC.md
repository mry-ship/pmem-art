---
id: 01M64C048QN1RSWAMAV56KJREC
module: feature.SkillsKit
entity: PadChangedCamera
kind: correction
status: active
supersedes:
- 01M642X9DXH0NFC3GC0GDS3ZJ4
anchors:
- skills_kit/converge.py#_resolve_pad_image
revision: git:a6d5ae4
author: yanghu
note_date: '2026-10-30'
summary: high/recompose 换机位后可垫换机位最高分
verify: high/recompose 有换机位证据时 pad=changed_camera；否则垫最初参考
applies: high/recompose 有参考图的闭环
---
用户2026-10-30明确取舍：合并GitHub最新时保留本地垫图——未换机位前仍垫最初参考；
轮次文本证明已换机位后可垫换机位最高分。
提示词里的「重构机位」本身不算证据（仍守 RecomposeEvidence）。
与 PadBestPlate「每轮只垫最初参考、禁止垫最高分板」在 high/recompose 已换机位场景冲突，以本条为准。
保留 AutoRecall 与 finish/showcase-gate。
