---
id: 01M872W9W51SRR2NRHK2S5VCS9
module: feature.SkillsKit.Converge
entity: ConvAssetId
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#ensure_conv_asset
- skills_kit/converge.py#_finish_write_final_slot
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 正式资产路径用内容哈希，final 只是可替换展示入口
verify: unittest tests.test_delivery_speed.TestStaleSlots.test_same_filename_assets_do_not_overwrite
  -q
applies: converge finish 把胜出图收进 assets 时
aliases:
- 同名覆盖
- asset_id
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：ensure_conv_asset 按 assets/{域}/{实体}/{原文件名} 复制，不同会话的同名文件会互相覆盖。
必须保持：正式路径是 assets/{域}/{实体}/id_{内容哈希}{后缀}。
同一哈希不重复写。
哈希路径上若已有不同字节，不覆盖，另写带大小的文件名。
winner.asset_image / asset_id 指向这份不可变文件。
final.* 仍可被结算覆盖，只作画廊展示，不是资产身份。
入口：skills_kit/converge.py ensure_conv_asset；_finish_write_final_slot。
