---
id: 01M759WH13V3BHHGJZ9EQTYFXQ
module: infra.Cli
entity: GenerateHook
kind: correction
status: active
supersedes:
- 01M735H9Z3MT3M2RXC9V2B9C5D
- 01M734JMPYA1ZXYRGF97P97X9J
- 01M7345BFWQYKHWFAZKMYMHHFN
anchors:
- pmem_art.py#cmd_hook
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: pre-gen 永不灌词；已删灌词死代码
verify: rg merge_block_into_image_args pmem_art.py 无命中；unittest tests.test_auto_recall.TestHookInjectsGenerateImage
  -q
applies: Cursor GenerateImage 出图与 cmd_hook/pre-gen 维护时
aliases:
- 永不灌入
- 删 merge_block_into_image_args
verified: '2026-11-11'
verified_at: '2026-11-11T21:41:56.506+08:00'
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧结论：默认不挂 pre-gen；或设 PMEM_ART_PRE_GEN_INJECT=1 才灌 Warm-Start；merge.* 另跳过灌入。
更正：cmd_hook(pre-gen) 永不写 updated_input；环境变量无效；已删除 merge_block_into_image_args。
记忆并入只认 converge generate / WARM_START_MERGED；认领只走 post-asset。
