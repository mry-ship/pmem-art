---
id: 01M83R48ETMPH5CVZB1K1N1Y51
module: infra.Scripts
entity: LayerSplitPipeline
kind: correction
status: active
supersedes:
- 01M83QSH9QKNV4WVEK7651WARS
anchors:
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆层根因在定块：前景横带和小屋吞邻框
verify: 对照 split_plan.json 的 foreground 横带 z=6 与 main_house 大框；树屋单件重画内容正确；_crops_guide.png
  在出图前已显示吞邻
applies: 评判这次 layer.split 展陈：裁切重画是正常做法，根因看 split_plan 的框和 z
aliases:
- 定块
- 层级
source:
  kind: human
---
展陈童话花园拆层的根因在出图前的定块，不在裁切重画本身。
前景被切成下半幅横带且 z 最高，草地、整条路、蘑菇桌绑在一层，压住池塘、屋脚和鼹鼠；
小屋框吞进树枝和路，路又同时写进小屋和前景的 keep。
这种框重画只能交出一块新的完整板，所以内容换样和层级盖错是同一次定块造成的。
对照：树屋框是单件，重画内容就对，略小可以放大。
_crops_guide.png 在 isolate 之前已经画出这些吞邻框。
