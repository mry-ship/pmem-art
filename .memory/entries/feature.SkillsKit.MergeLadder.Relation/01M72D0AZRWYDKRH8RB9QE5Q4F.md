---
id: 01M72D0AZRWYDKRH8RB9QE5Q4F
module: feature.SkillsKit.MergeLadder.Relation
entity: HarborChainBreaks
kind: conclusion
status: active
supersedes: []
anchors:
- docs/MERGE_MULTI_LENS.md
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 掏空、转角度、挂配料、零件装箱都不算合成下一档
verify: 重画关系稿里相邻两档能用「两件这个做成那个」说通，且末档不是前一档的零件堆
applies: 重画露莓、浇水、管乐这三张 Gossip Harbor 竖屏整表时。
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
竖屏 4×2 重画后，画幅和换物种问题减轻了，但合两下仍有几步说不通。
果酱 sheet_r2：第 2 格是掏空的莓，两颗整莓合成不出一个洞；第 3 格是一碗心形块；第 5 格仍是第 4 格那只杯，只在杯沿挂了一颗莓；第 6 格变成白奶油布丁，离开露莓；第 7 格挞夹在两只蛋糕中间，第 8 格又回到蛋糕。
浇水 sheet_r3：前三格都是同一把壶换角度，第 1 格已经有莲蓬头；末格是小车里散放着壶、卷管和喷头，不是一件合成后的货。
管乐 sheet_r4：直管之后跳成号角，再跳回长笛；第 5 格是两根管子捆在一起；末格是另一台棕色手摇风琴。
必须保持：下一档是两件当前货做成的下一件货。禁止掏空、只转角度、同一容器挂一颗配料、把前几档零件放进箱子。
