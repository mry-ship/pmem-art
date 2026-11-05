---
id: 01M6NJCA7J2JGGZPVA0BEFKNZT
module: feature.SkillsKit
entity: ShowcaseGateProcessBoard
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/showcase_gate.py#round_count
- skills_kit/showcase_gate.py#audit_showcase_html
- skills_kit/route_bank.py#distill_entries
- .cursor/hooks.json
revision: git:28ae4ac
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: Fix5：过程板闸门认第N轮只审胜出；交付词入库；pre-gen failClosed
verify: pyw -3 -u -m unittest tests.test_showcase_gate tests.test_route_bank_delivery
  -q
applies: converge finish / 过程板展陈 / GenerateImage Hook / merge 交付词路由检索
verified: '2026-11-05'
verified_at: '2026-11-05T20:36:04.523+08:00'
---
需求来源：Round5 审计——真实过程板文案「第 N 轮 · score」被 round_count 跳过「第」解析成 None，且闸门扫全部 figcaption，导致历史低分卡拖垮整页。

必须保持：
1. showcase_gate 识别「第 N 轮 · score」；过程板只审 figure.card.win，完成轮次取页上最大「第 M 轮」；展陈格（low · N 轮）仍按 caption。
2. GenerateImage pre-gen Hook failClosed=true，warm-start 未灌入则拦生图。
3. colloquial_expand 与 route_bank 蒸馏后须含 整表/overview_sheet/per_cell/一档一张/shop_ladder；蒸馏按路由×桶×交付指纹分层，避免同 route 步进抽样挤掉交付词。
4. 档位回归样张 docs/showcase/default_round/images/night_city_ref.png 存在，对应单测不再 skip。

适用：converge finish / 展陈 HTML / 路由检索 / GenerateImage Hook。
入口：skills_kit/showcase_gate.py；
skills_kit/route_bank.py distill_entries；
skills_kit/colloquial_lexicon.py；
.cursor/hooks.json；
tests/test_showcase_gate.py。
验证：pyw -3 -u -m unittest tests.test_showcase_gate tests.test_route_bank_delivery -q；
本机 boards 抽查约 29/30 OK（仅未满4轮且<9.5的真实未完成板 FAIL）。
