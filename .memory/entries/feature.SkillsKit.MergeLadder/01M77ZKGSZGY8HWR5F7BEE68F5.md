---
id: 01M77ZKGSZGY8HWR5F7BEE68F5
module: feature.SkillsKit.MergeLadder
entity: GhPadStyleLock
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/delivery_gates.py#generate_prefix
- skills_kit/delivery_gates.py#merge_follows_style_ref
- skills_kit/merge_relation.py#_MERGE_SURFACE
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 垫GH真机时generate改灌垫图锁画风短句，跳过缺省糖釉
verify: unittest test_merge_without_style_is_gossip_harbor；test_photo_microdetail_in_silhouette_blocked
applies: merge 合成梯；有风格/真机垫图或纯文缺省
source:
  conversation: fda824e5-6393-4f0c-859e-6a0bf93b50bd
---
需求来源：硬料海鲜对标后玩家要求垫GH真机；缺省软立体糖釉长句与截图货面打架，缺陷含木纹还误报未指定风格偏写实。
必须保持：merge_follows_style_ref（ref_image/参考路径/goal垫真机）为真时 generate_prefix 注入垫图锁画风短句而非 _MERGE_SURFACE；
judge_gate_notes 不再因木纹等词报偏写实；
缺省 _MERGE_SURFACE 改为块面高光并对齐真机完成度表述；
档位焦斑鳞片仍拦，柠檬配菜在垫真机 surface 下放行。
入口：skills_kit/delivery_gates.py generate_prefix/judge_gate_notes；merge_relation photo_microdetail_hits。
