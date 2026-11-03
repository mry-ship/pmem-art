---
id: 01M6ED8WQ0WGQAXCYRBJ3VT59C
module: infra.Scripts
entity: LayerSplitPlanBoxes
kind: exclusion
status: active
supersedes: []
anchors:
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-02'
summary: 禁止整表凭感觉微调 split_plan；只改被点名的边
verify: 改完只动一个 id 的一条边并重出 _crops_guide
applies: 定块/改脚印时
---
排除：Agent 看图后对整张 split_plan 做「全面微调」。
归一化框无像素尺，整表重写常把已合格框拧坏、松框互相吞并，准度不如旧紧脚印。
应先紧（pad≤0.02）→setup 看 guide→用户点名哪条边→只改该边 0.02～0.04。
