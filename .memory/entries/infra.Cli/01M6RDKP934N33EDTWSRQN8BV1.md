---
id: 01M6RDKP934N33EDTWSRQN8BV1
module: infra.Cli
entity: AtlasRevealApi
kind: feature
status: active
supersedes:
- 01M6RCZ5R4E981V3F5GZF9QN8J
anchors:
- atlas_reveal.py#promote_final
- atlas_reveal.py#_static_allowed
- atlas_reveal.py#_loopback_caller
- skills_kit/converge_loop.py#session_json_path
- skills_kit/converge.py#_session_file
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 会话 id 不能穿出 converge；跨站不能改图；源码不从工作台读出
verify: py -3 -u -m unittest tests.test_atlas_all_images.AtlasAllImagesTests.test_promote_final_copies_over_slot_and_keeps_session
  tests.test_atlas_all_images.AtlasAllImagesTests.test_reveal_serves_workbench_html_over_http
  -q
applies: pmem_art atlas 守护进程在跑、或 converge 写会话文件时
aliases:
- 本机接口
- CORS
- 路径穿越
- promote_final
- session_id
source:
  conversation: 2fb9d6ff-529d-4817-aa0f-d09fd39d062b
---
会话 id 必须落在 .memory-art/converge 这一层。
session_json_path 拒绝分隔符和 ..；
promote_final 遇到这种 id 直接失败，不改写目录外的 JSON。
converge 报告改从已校验的会话文件同目录取名。
静态托管只放行 html/js/css/图片，加上 .memory-art/atlas_data.json 和垃圾箱 manifest.json。.py、.md 和 taste.json 不再从本机接口读出。
POST 删图/提升，以及 GET 定位，只接受没有 Origin、Origin 为 null（file://）或 http://127.0.0.1 与 localhost。
跨站网页的 Origin 回 403。
工作台页面仍能取 atlas_data.json 和图片。
