---
id: 01M7SZ9NF037J0KKWZYQ4H1H2Y
module: infra.Scripts
entity: LayerSplitPipeline
kind: feature
status: active
supersedes:
- 01M6EB2YT4GW513SNSBXM2TXSX
anchors:
- .cursor/skills/pmem-layer-split/SKILL.md
- scripts/pmem_layer_split/isolate.py#_find_image_gen
- scripts/pmem_layer_split/isolate.py#isolate_layers
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-19'
summary: 拆层优先 gpt-image-2.5，无通路退 Cursor 生图；不对人展示密钥
verify: SKILL 引擎节含优先 gpt-image-2.5 与 Cursor 回退；全文无 config.json/密钥展示句；_find_image_gen
  可返回 None
applies: 执行 /pmem-layer-split 隔离出图时
aliases:
- layer-split引擎
- 拆层Cursor回退
source:
  conversation: 11091f6c-97d6-42cb-87f7-e01a76473eac
---
需求来源：画师要求改技能——不要展示密钥；网络优先 gpt-image-2.5，没有就用 Cursor 生图。
必须保持：隔离引擎优先级为 gpt-image-2.5（apikey-image）→ Cursor GenerateImage；
Cursor 无真透明时用纯黑隔离底、禁止后抠；
对人回复禁止展示/复述/索要密钥或 config；
CLI 入口 pyw -3 -u scripts/run_pmem_layer_split.py。
行为：isolate 找不到 gpt-image-2.5 通路时写 needs_cursor_gen 并打印 NO_GPT_IMAGE_25，不硬崩；API 调用失败同退 Cursor。
入口：.cursor/skills/pmem-layer-split/SKILL.md；scripts/pmem_layer_split/isolate.py#_find_image_gen。
