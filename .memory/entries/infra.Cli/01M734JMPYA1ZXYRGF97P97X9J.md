---
id: 01M734JMPYA1ZXYRGF97P97X9J
module: infra.Cli
entity: GenerateImageHook
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py#cmd_hook
- pmem_art.py#is_generate_image_tool
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: merge.* pre-gen 跳过 Warm-Start 灌入 GenerateImage
verify: unittest tests.test_auto_recall.TestHookInjectsGenerateImage.test_merge_module_skips_warm_start_inject_into_generate_image
applies: pre-gen + GenerateImage 且会话 module 以 merge. 开头时
aliases:
- merge 跳过 hook 注入
- 不灌 Warm-Start
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
需求来源：阶段1——merge 会话里 hook 再把 Warm-Start 灌进 GenerateImage description，常与手写 brief / GH 表面锁打架。
必须保持：module.startswith("merge.") 时 pre-gen 不写 updated_input；
agentMessage 标明跳过；
非 merge 仍可 prepend Warm-Start。
converge generate 仍并入（经冲突过滤后的）pack，本改动只跳过 hook 改写 description。
入口：cmd_hook(pre-gen)。
