---
id: 01M70QA0X3HFJATY712YQA3KFX
module: feature.SkillsKit.Showcase
entity: ShowcaseMissingImageFile
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/showcase_gate.py#audit_showcase_file
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: showcase-gate 校验本地 img src 文件存在
verify: python3 -m unittest tests.test_showcase_gate -q
applies: python3 pmem_art.py showcase-gate --html <page>
---
必须保持：audit_showcase_file 除分数/轮次闸外，还拒绝 HTML 内相对路径指向不存在的本地图片（http/data 跳过）。
防止断链页仍展示过闸。
入口：skills_kit.showcase_gate.audit_showcase_file。
