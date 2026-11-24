---
id: 01M872DY0YGC05KDE0KW2K7A0F
module: feature.SkillsKit
entity: PhysicalDecode
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/image_gates.py#_inspect_image_physical_traits
- skills_kit/image_gates.py#_decode_image_pixels
- skills_kit/validate_params.py#_physical_image_gate
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 图片有效必须解码像素；字节熵不能单独放行
verify: unittest tests.test_hard_pits_gates.TestDecodedPhysicalGate tests.test_param_validation.TestGateFixes.test_webp_header_has_resolution
  -q
applies: converge 登记成图、judge 和轮次图片是否算真图时
aliases:
- 字节熵
- verify
- 有效像素
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：物理验收只读文件头尺寸和前 64KB 字节熵，坏图、高熵空图、几乎全透明的图都能过。
必须保持：_inspect_image_physical_traits 先 Pillow verify() 再 load()。
宽高用解码后的像素；
头部尺寸只记入 header_width/header_height。
解码失败就拒绝登记或过线。
有 alpha 时按资产类型查有效像素比例（图层/透明件 1%，图标和普通图 0.5%）。单一颜色铺满整幅（空白比例 ≥0.985）也拒绝。
字节熵仍写入 color_entropy，不得因为熵高就放行，也不得只因为熵低就拦下已解码且有内容的图。
入口：skills_kit/image_gates.py _inspect_image_physical_traits；
skills_kit/validate_params.py _physical_image_gate。
生图登记与 judge 都走这道闸。
