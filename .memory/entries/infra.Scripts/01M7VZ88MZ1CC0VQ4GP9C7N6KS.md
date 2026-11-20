---
id: 01M7VZ88MZ1CC0VQ4GP9C7N6KS
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes: []
anchors: []
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 仅用Cursor GenerateImage黑底隔离时，近黑→alpha+alpha=1 letterbox可让gate全ok；幽灵MAE常在48线附近或以上，重抽易因换样/autofit缩框而更差。
verify: viking_camp_10 layer_status gate ok=10；_ghost_qa mae≈48–60；_ingest_cursor.py
source:
  conversation: 0d13db42-21e6-4167-90ba-7e33e023b78b
---
玩家强制只用Cursor生图（不用gpt-image）拆viking_camp_10（bg+9）。
流程：setup脚印 → GenerateImage垫_crops黑底隔离 → 近黑→alpha（thr≈28）+按脚印asp letterbox（alpha=1垫边）→ compose/gate/qa/emit。
结果：GATE可10/10 ok；幽灵MAE首轮≈48.3（贴fail线），后续重抽热点层后MAE常升到59+（换样+autofit把篝火/灯桩缩到fill≈0.43）。
排除：为压幽灵而反复换样重抽反而变差；cabin近全黑废图勿入库。
交付仍交_compose_mid + stack.html + new/散层，并标明幽灵未过线。
