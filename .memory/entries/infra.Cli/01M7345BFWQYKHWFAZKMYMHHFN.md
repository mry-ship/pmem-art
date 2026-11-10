---
id: 01M7345BFWQYKHWFAZKMYMHHFN
module: infra.Cli
entity: GenerateHook
kind: feature
status: active
supersedes: []
anchors:
- lifecycle.py#ensure_cursor_stubs
- pmem_art.py#cmd_hook
- .cursor/_pre_gen_hook_disabled.txt
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: GenerateImage pre-gen 默认关闭；install 不再装回
verify: unittest tests.test_cursor_hooks_stubs tests.test_auto_recall.TestHookInjectsGenerateImage.test_pre_gen_inject_off_by_default；.cursor/hooks.json
  preToolUse 无 hook pre-gen
applies: Cursor GenerateImage 出图；skills --install / ensure_cursor_stubs 刷新 hooks 时
aliases:
- 停 pre-gen
- 关掉 Warm-Start 灌入
- PMEM_ART_PRE_GEN_INJECT
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
需求来源：对照试验确认 pre-gen 灌 Warm-Start 会污染 GenerateImage 提示词；玩家要求默认关掉且 install 不得装回。
必须保持：ensure_cursor_stubs 的 art preToolUse 默认不含 pmem_art.py hook pre-gen；
刷新 hooks 会去掉旧 pre-gen 条目。
cmd_hook(pre-gen) 即使被手工挂上，默认也不写 updated_input，除非环境变量 PMEM_ART_PRE_GEN_INJECT=1；
merge.* 额外硬跳过。
converge generate 仍并入已过滤 Warm-Start pack。
post-asset / stop / art_shell 照常。
入口：lifecycle.ensure_cursor_stubs；pmem_art.py hook pre-gen。
