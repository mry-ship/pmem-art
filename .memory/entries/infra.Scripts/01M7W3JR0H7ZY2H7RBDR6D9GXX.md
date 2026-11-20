---
id: 01M7W3JR0H7ZY2H7RBDR6D9GXX
module: infra.Scripts
entity: LayerSplitPlanBoxes
kind: correction
status: active
supersedes:
- 01M7VZF63K79PYM64HQS136WFY
anchors:
- scripts/pmem_layer_split/defaults.py
- scripts/pmem_layer_split/calibrate.py
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: setup固定pad0.10+isolate0.08；禁贴边狂扩；plan框不回写
verify: viking setup 后 heroine area≈0.61 且非 1.0；split_plan.crop 保持原稿；二次 setup 框不继续胀
applies: 执行 /pmem-layer-split setup 时
aliases:
- 框太紧
- pad0.10
- 切肢
source:
  conversation: 8bf3f9f2-0d6e-45db-b55e-017394ead677
---
玩家反馈框仍切肢。试过贴边自动扩，忙碌游戏图会扩成满幅并污染 split_plan。
更正：
1) setup 对 plan 固定 expand CROP_PAD_PLAN=0.10；isolate 裁切再 +0.08；不做迭代贴边狂扩。
2) 禁止把扩后框写回 plan.crop（只写 _truth_crop/_isolate_crop），否则反复 setup 会越扩越大。
3) Agent 定块仍须先包全；柔边按 0.10–0.12 写。
入口：defaults.CROP_PAD_*；calibrate setup 循环；SKILL §1.1。
