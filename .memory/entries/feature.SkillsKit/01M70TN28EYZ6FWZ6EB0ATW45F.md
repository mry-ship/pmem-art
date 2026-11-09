---
id: 01M70TN28EYZ6FWZ6EB0ATW45F
module: feature.SkillsKit
entity: SkillsKitAutoRoute
kind: feature
status: active
supersedes: []
anchors:
- .memory/modules.yaml
- tests/test_skills_kit_module_paths.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: SkillsKit 子模块 paths 驱动闸门自动存取归位
verify: tests.test_skills_kit_module_paths；pmem search --path <文件> 模块名正确
applies: Cursor/pmem hook 改 skills_kit 或 .agents/skills/pmem-* 时
---
需求来源：分层后要保证以后自动存记忆能取、能存对位置。
必须保持：modules.yaml 为每个 SkillsKit 子模块登记互不重叠的 paths；
skills_kit 下每个 .py 都能 module_for_path 命中；
各 /pmem-* 的 .agents/.cursor skills 目录挂到对应子模块；
Prompt/Critique/Coach 已转正（非 candidate），可直接写入。
适用条件：本仓库同时使用 pmem 闸门与 SkillsKit 分层期间。
入口：改代码前 search_memory(path=…) 或 pmem search --path；写记忆用闸门提示的子模块，Merge 按下沉规则。
