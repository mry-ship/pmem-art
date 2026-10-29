---
id: 01M643RS18X7D2SYWRT9GXHCYF
module: infra.Cli
entity: GenerateHook
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py#cmd_hook
- pmem_art.py#parse_hook_payload
- pmem_art.py#image_gen_arg_view
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: GenerateImage Hook必须用updated_input灌Warm-Start，Write不改内容
verify: python -m unittest tests.test_auto_recall.TestHookInjectsGenerateImage tests.test_auto_recall.TestHookPayload
  -v
applies: Cursor preToolUse 触发 pmem_art.py hook pre-gen 时
aliases:
- updated_input
- GenerateImage
---
需求来源：Cursor preToolUse 实际 stdin 是 tool_name + tool_input，旧 Hook 只读 toolName/arguments，GenerateImage 灌不进记忆。
必须保持：cmd_hook 识别 GenerateImage 以及 CallDynamicTool 嵌套的 GenerateImage arguments，把 Warm-Start 写入 description 或 prompt。
同时输出 agentMessage 与 agent_message。hooks.json 里 pmem-art pre-gen 的 failClosed 仍为 false，Hook 失败不能挡生图。
给用户的包仍只含 pmem-art Hook，不把 mry-ship/pmem 做成运行时依赖。
入口：python pmem_art.py hook pre-gen。
