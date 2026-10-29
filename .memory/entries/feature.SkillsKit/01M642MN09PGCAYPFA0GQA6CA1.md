---
id: 01M642MN09PGCAYPFA0GQA6CA1
module: feature.SkillsKit
entity: MergeLadder
kind: exclusion
status: active
supersedes:
- 01M642JD0079FCD04799FWEQMT
anchors:
- skills_kit/merge_relation.py#split_sheet_grid
- skills_kit/skill_specs.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 禁止默认写实、糖果焊蛋糕、letterbox切顶、contain贴边和CSS假居中
verify: 绣球/糖签完整且主体在格心；糖果链不含蛋糕马卡龙纸杯蛋糕
applies: pmem-merge-ladder 关系稿与组图切开交货
aliases:
- 切顶
- 白模
- 产品实拍
---
试过默认产品实拍、把蜜桃糖焊进马卡龙/纸杯蛋糕、把16:9切成2×4竖矩形再 letterbox 成正方形、整格 contain 进正方形、靠 HTML object-fit 假装居中、用 normalize 交差。
结果是风格偏离竞品、前几档合成说不通、绣球和糖签被切顶、花贴在格子左上、展陈8列挤成邮票。
排除：玩家没要写实时不要默认写实静物；
不要把 Sweet Candies 焊进 Sprinkle Cakes；
不要按垂直居中的 letterbox 正方形去切（模型常把方卡铺在每行顶部）；
不要只 contain 不居中；
不要用 CSS 掩盖像素偏移；
不要靠归一化代替切对。
交货只能是切开后居中的八张正方形。
