---
id: 01M643RHM64GHP855EWZHJ1ZVF
module: feature.SkillsKit
entity: RecallGap
kind: correction
status: active
supersedes:
- 01M6432Z1VE3MCX67H8K6NHV8S
anchors:
- skills_kit/converge.py#cmd_converge
- pmem_art.py#cmd_hook
- feedback.py#infer_module_from_text
- improve/warm_start.py#merge_warm_start_prompt
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 跑skill时必须自动读.memory-art，禁止再靠手贴Warm-Start
verify: python -m unittest tests.test_auto_recall -v
applies: Cursor里跑 /pmem-draw / 合成梯 / converge 生图时
aliases:
- 不查记忆
- 看不到记忆
- Warm-Start
- 自动召回
---
旧结论认为跑 skill 时 pmem-art 会写记忆但不会强制读，Warm-Start 要靠 Agent 手贴，Hook 猜错模块就空召回。
这条已经不成立。跑 /pmem-draw、合成梯、converge 生图时必须自动读 .memory-art。
converge generate 把会话 Warm-Start prompt_block 并入 composed_prompt，并回显「已自动并入记忆」。
pre-gen Hook 解析 Cursor 的 tool_name/tool_input（含 CallDynamicTool 嵌套 GenerateImage），用 updated_input 把同一包灌进 description/prompt。
没有活跃会话时按提示词猜模块：合成梯/糖果/道具走 prop，不再落到 brand.WorldStyle。
Agent 手贴不再是召回路径；没并入算 bug。
recipe、红线、口味仍只进 .memory-art，不要抄进 .memory。
没有 converge start 时 generate 仍必须失败，不能为了灌记忆悄悄建会话。
合格线仍是 >=9.6、最多 4 轮。
