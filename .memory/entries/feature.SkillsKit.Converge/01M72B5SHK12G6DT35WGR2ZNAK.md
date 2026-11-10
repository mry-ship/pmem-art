---
id: 01M72B5SHK12G6DT35WGR2ZNAK
module: feature.SkillsKit.Converge
entity: PadOrientation
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge_policy.py
- skills_kit/converge.py
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 竖屏垫图不能加边填成横画布
verify: pyw -3 -u -m unittest tests.test_delivery_gates.DeliveryGateTests.test_portrait_pad_cannot_be_filled_into_landscape
applies: 有垫图的 converge 生成。同方向的小幅加边仍允许。
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
玩家指出 Gossip Harbor 商店图是竖屏，成图却是横版。根因是交付先写死 4:3 或 16:9，ensure_aspect_matched_ref 再把竖图加边填成横画布。
必须保持：垫图与目标画幅一个横一个竖时直接拒绝，不再生成 *__ar_4x3 或 *__ar_16x9。竖屏垫图用 9:16 或 3:4。
验证：tests.test_delivery_gates.DeliveryGateTests.test_portrait_pad_cannot_be_filled_into_landscape
