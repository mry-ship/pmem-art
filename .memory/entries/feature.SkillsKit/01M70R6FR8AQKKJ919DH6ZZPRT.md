---
id: 01M70R6FR8AQKKJ919DH6ZZPRT
module: feature.SkillsKit
entity: AlphaByEngine
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/alpha_policy.py#engine_supports_alpha
- skills_kit/export_mode_c_icon.py#as_delivery_rgba
- skills_kit/skill_specs.py
- pmem_art.py
- skills_kit/reasonableness_gate.py#_heuristic_issues
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: Cursor无alpha出隔离底；透明引擎才真alpha；禁止后抠
verify: python3 -m unittest tests.test_alpha_policy -q；skill/规则含不支持真透明；export 默认不抠；validate
  仅 alpha_strict 才拒缺 alpha
applies: 出图走 Cursor GenerateImage 或 gpt-image 等第三方时；icon.c/UI组件表/merge per_cell/普通图透明意图；validate
  无 alpha_strict 时不硬拒缺通道
---
需求来源：画师反馈 Cursor GenerateImage 不支持透明度，项目里却常后抠冒充真 alpha；gpt-image 等才支持直接出透明。
必须保持：默认 Cursor 路径把「透明底」改写成不透明隔离底（默认纯黑），禁止成图后再抠色/抠角/本地挖洞；支持透明的引擎（gpt-image 等）才直接要真 alpha PNG。
行为：skills_kit/alpha_policy.py 按引擎分流；
skill_specs / 总规则 / agent/prompt 写清；
icon.c 合理性闸认纯黑隔离或透明措辞；
export_mode_c_icon 默认不抠；
validate 仅当模块 alpha_strict 才因缺通道失败（alpha_required  alone 接受 opaque isolation）。
入口：出图合同与 /pmem-icon Mode C、UI 组件表、merge per_cell；skills --install 同步。
