---
id: 01ART006EXPRCORRECTION
module: character.Astra.Expressions
entity: ExpressionSheet
kind: visual_correction
status: active
note_date: '2026-10-23'
verified: '2026-10-23'
summary: 表情差分瞳光色阶修正；惊愕冷启动稿作 rejected 反例保留（fixture）
verify: shock_draft 保持 role=rejected 且不触发 STALE
assets:
  - path: assets/character/astra_expressions_2x2.png
    role: approved
    caption: "已验收 2x2 表情差分合集（1024x1024 RGBA）"
  - path: assets/character/astra_expr_shock_draft.png
    role: rejected
    caption: "反例样张：768x768 RGB（缺 Alpha）——有意保留作 Don't"
---
fixture: rejected counter-example must not make the entry STALE.
