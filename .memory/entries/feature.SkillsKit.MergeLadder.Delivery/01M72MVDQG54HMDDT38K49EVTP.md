---
id: 01M72MVDQG54HMDDT38K49EVTP
module: feature.SkillsKit.MergeLadder.Delivery
entity: VolumeGateVsBenchmark
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#audit_overview_sheet
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: GH 自家咖啡链过不了我们的邻档框高闸；该闸逼出跨轮拼贴
verify: 去掉卡底蓝色量 assets/refs/merge_chain_study/reddit_ybo44puiahue1.jpg 前 12 卡主体框高；看
  merge_wind/final.jpg L6 下方残片
applies: 休闲 merge 整表 overview_sheet 用像素框高闸验收时
aliases:
- 体量闸
- 框高阶梯
- 拼贴整表
---
实测 Gossip Harbor Decaf Coffee 收藏页 12 档：主体占卡高 0.83/0.87/0.87/1.00/0.83/0.87/0.92/0.88/0.90/0.90/0.94/0.94，不单调，邻档差多为 0~0.05，L4→L5 还缩小 0.17。
竞品升级靠剪影与件数（加碟、加糖勺、拉花、圣代），不靠放大。
我们 audit_overview_sheet 要求邻档框高每档 +0.04（OVERVIEW_MIN_STEP）且末档最大，竞品自己过不了。
生图模型控不住精确比例，agent 因此写 _make_volume_final.py 之类脚本，从多轮整表抠格缩放拼成 0.42→0.96 阶梯，留下残片（果酱 L3 下方半个杯口、管乐 L6 下方一截风琴）和切顶（管乐 L8）；
管乐拼贴版仍被判 9.51 过线。
影响：merge 整表"效果差"的主因之一是这道闸逼出的拼贴，不是关系稿。
