---
id: 01M6M6532THN798DFRFDT1B2QG
module: infra.Cli
entity: AtlasWorkbench
kind: correction
status: active
supersedes: []
anchors:
- pmem_art.py#_guess_final_image
- pmem_art.py#attach_converge_prompt_traces
- build_atlas.py#sessionOfAsset
- skills_kit/converge.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 终稿槽 final.jpg 必须挂 converge 会话，rN 不能抢 final
verify: python -m pytest tests/test_atlas_all_images.py -k final_slot -q；点 assets/ui/mainmenu/tilematch/final.jpg
  进化对照可见 r1–r4
applies: 工作台定稿点「详情·进化对照」时
aliases:
- 进化对照空
- 过程图看不到
source:
  conversation: 8e3ae576-2e1f-44e5-aebc-a9b80861a3a6
---
现象：Tile Match 主菜单点工作台定稿「详情·进化对照」为空。
根因：
  1) _guess_final_image 在 stem=r3 时先命中同目录 r3.jpg，排在 final.jpg 之前；
  2) finish 只写 winner 对象、不写顶层 winner_image/final_image，也不保证复制 final.*；
  3) 手工 final.jpg 未 stamp converge_session_id。
修法：同目录优先 final.* / *_final.*；
纯 rN stem 不得回落成自身；
attach 从 winner.image 取胜出轮并为 final 槽打会话；
有独立 final 时 rN 保持 process+隐藏；
finish 复制 final.* 并落盘 winner_image/final_image；
前端 sessionOfAsset 同目录 final 兜底。
排除：继续把 r3.jpg 当终稿文件名、或点 final.jpg 无会话。
