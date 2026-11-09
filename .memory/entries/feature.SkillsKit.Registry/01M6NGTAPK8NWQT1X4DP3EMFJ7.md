---
id: 01M6NGTAPK8NWQT1X4DP3EMFJ7
module: feature.SkillsKit.Registry
entity: SkillDocAuditFix20261105
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- skills_kit/skill_registry.py
- tests/test_skill_router.py
revision: git:28ae4ac
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 技能文档审计项落地：icon并列、atlas改http、merge整表质检、draw强制route等
verify: unittest tests.test_skill_router；.cursor/skills 与 registry Mode 标题；17项 verify
applies: 改 /pmem-* 技能文案或 install 后
aliases:
- SkillDocAuditFix
---
需求来源：玩家审计十技能后要求都修并复检。必须保持：
  1) icon Mode A/B/C 三个并列 ##，交付清单分模式；
Mode A 多维透镜在 bash 外。
  2) atlas 告知用 atlas 打印的 http://127.0.0.1，禁止只双击 art-atlas.html。
  3) merge overview_sheet 出图前 reasonableness（sheet_safe_zone）+ 固定验收清单，≤3 次重出。
  4) pmem-draw / 点名支必须先 route 写闸门；
禁止默认 skip-route-gate。
  5) critique 统一六维；
红线仅玩家认可/反复硬伤才入库，禁止仅因外审<9.5刷红线。
  6) ui 显式 concept-only vs full kit。
  7) prompt 选定后出图先 route。
  8) simultaneous_pixels 明示暂不支持。
入口：改 skills_kit/skill_specs.py 后 skills --install；
tests.test_skill_router。
