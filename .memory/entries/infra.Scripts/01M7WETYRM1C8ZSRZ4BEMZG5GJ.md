---
id: 01M7WETYRM1C8ZSRZ4BEMZG5GJ
module: infra.Scripts
entity: LayerSplitPipeline
kind: correction
status: active
supersedes:
- 01M7W6QV6HYQDAE7H3A0RRCGMF
anchors:
- scripts/pmem_layer_split/defaults.py
- scripts/pmem_layer_split/gate.py#run_gate
- scripts/pmem_layer_split/qa.py#apply_ghost_dirty
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 拆层根因加固：pad减半、scale_mul≥0.75、幽灵回灌、中景必有槽
verify: pyw -3 -u assets/viking_camp_10/_skill_hygiene_check.py → RESULT PASS；GATE.scale_mul_min==0.75；CROP_PAD_PLAN==0.05；SKILL
  无 ISOLATE_EXTRA=0.08
applies: 执行 / 维护 /pmem-layer-split 定块、setup、gate、qa、pipeline 时
aliases:
- scale_mul
- 脚印过松
- 中景雪松
- 幽灵回灌
- 技能体检
source:
  conversation: 2f354fef-48d1-45fb-b2ba-e9001d9d3e16
---
玩家要求从技能根上修 viking 拆层（gate ok 但幽灵差），并体检无错漏。

根因与合同：
1) Agent 已垫≥0.08 后 setup 再叠 PLAN=0.10+ISOLATE=0.08 → 脚印撑爆 → scale_mul≈0.66。现 PLAN=0.05、ISOLATE_EXTRA=0.05、TIGHTEN=0.06。
2) GATE.scale_mul_min=0.75（gate.py 缺省回退亦 0.75；0.82 会误杀遮挡补全≈0.78）。
3) qa.apply_ghost_dirty：层 MAE>52 回灌 dirty；pipeline gate 干净后仍跑幽灵。gate ok ≠ 可交件。
4) 可见中景英雄树必须有 module；陶罐可并帐篷。
5) ISOLATE 第7条锁场景光；load_json utf-8-sig。

体检：三份 SKILL 同哈希；§2 旧 ISOLATE=0.08/TIGHTEN≈0.08 已改齐；_skill_hygiene_check RESULT PASS。

viking：clay_pot→mid_pines；gate 10/10；幽灵≈47.5 warn。
