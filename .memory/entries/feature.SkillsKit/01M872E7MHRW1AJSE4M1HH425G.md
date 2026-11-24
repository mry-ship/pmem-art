---
id: 01M872E7MHRW1AJSE4M1HH425G
module: feature.SkillsKit
entity: PhysicalDecode
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/image_gates.py#_inspect_image_physical_traits
- skills_kit/validate_params.py#_physical_image_gate
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 不能用文件头尺寸加字节熵证明图片有效
verify: unittest tests.test_hard_pits_gates.TestDecodedPhysicalGate -q
applies: 改图片物理闸或登记成图前的文件检查时
aliases:
- 字节熵
- 文件头
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
排除：只解析 PNG/JPEG/WebP 头部宽高，再算前 64KB 的香农熵，用这两项决定图是否真的。
头部尺寸正确时像素仍可以坏；熵够高时画面仍可以几乎全空；透明图的有效像素可以极低；文件在但解码失败。
正确做法是 Pillow verify() 加 load()，再按资产类型看 alpha 覆盖和整幅空白比例。字节熵只保留为旁证。
