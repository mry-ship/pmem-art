---
id: 01M7MWNZ4810QND6M8DCGMDJV4
module: feature.SkillsKit.Converge
entity: EmitPromptMainChain
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
- pmem_art.py
- tests/test_converge_emit_prompt.py
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: generate --emit-prompt 先出最终Prompt再登记成图
verify: py -3 -m unittest tests.test_converge_emit_prompt -q
applies: 日常交付出图主链需要先拿最终 Prompt 再生图时
aliases:
- emit-prompt
- 先出Prompt
- 无图出Prompt
verified: '2026-11-23'
verified_at: '2026-11-23T23:14:23.694+08:00'
source:
  conversation: ecc26a91-afaa-451d-a24e-bcc932bdcb45
---
需求来源：日常交付墙钟深度优化（消灭 stub 骗闸与无图过不了物理闸）。
必须保持的行为：
1) `converge generate --emit-prompt`：装配+Warm-Start 并入后打印 FINAL_PROMPT_SHA1 与「最终 Prompt（出图须用这句）」；
   写入 pending_final_prompt / sha1 / round；
   不登记 rounds；
   不过输出物理闸；
   禁止与 --image 同开。
2) 随后 GenerateImage 必须逐字用该最终 Prompt；
   再 `converge generate --image` 登记；
   `--prompt` 为空且同轮有 pending 时复用 pending（sha 一致），登记成功清 pending。
3) 无 --emit-prompt 且无 --image 时登记失败并提示改用 emit-prompt。
适用条件：日常 Cursor GenerateImage / 外部生图主链。
入口：pmem_art.py converge --emit-prompt；skills_kit.converge.cmd_converge(emit_prompt=True)。
