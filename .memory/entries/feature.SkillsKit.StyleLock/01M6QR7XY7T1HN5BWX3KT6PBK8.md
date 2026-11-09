---
id: 01M6QR7XY7T1HN5BWX3KT6PBK8
module: feature.SkillsKit.StyleLock
entity: StyleLockNormalizeFold
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/colloquial_lexicon.py
- skills_kit/agent_router.py#_wants_style
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 口语折叠会毁掉锁风格触发句
verify: pyw -3 -u pmem_art.py route --text 以后按这张画 --brief 应走 style.lock 而非普通图
applies: 改 route_normalize / colloquial_lexicon / _wants_style 时
---
normalize 把「按这张」折成「参考这张」后，_wants_style 认不到「以后按这张」，plan_route 落到普通图；
vague ask 只软拦 execute_ok，底层 plan 仍错。
复现：以后按这张画 → 以后参考这张画 → draw.ordinary。
