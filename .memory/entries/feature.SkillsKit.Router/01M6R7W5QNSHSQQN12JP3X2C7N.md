---
id: 01M6R7W5QNSHSQQN12JP3X2C7N
module: feature.SkillsKit.Router
entity: RegistryFilePathNeutral
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_registry.py#build_registry
- skills_kit/skill_registry.py#_icon_routes
- skills_kit/skill_specs.py
- tests/test_skill_router.py
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: registry file 字段改平台中性 skills/<name>/SKILL.md；agent desc 瘦身到 262 字
verify: pyw -3 -u pmem_art.py skills --install 后 registry.json routes[0].file=="skills/pmem-ui/SKILL.md"；三平台根下均
  os.path.exists 为真；unittest tests.test_skill_router 通过
applies: 改 skill_specs/skill_registry 里 routes file 字段或 agent description 时
---
registry.json 的 routes[].file 字段从硬编码 ".cursor/skills/<name>/SKILL.md" 改为平台中性相对路径 "skills/<name>/SKILL.md"（build_registry 三处：_icon_routes 固定串、draw 循环、_ONE_SECTION 循环）。
原因：三平台（.cursor/.claude/.agents）副本字节一致，一份 registry.json 写入三目录；
硬编码 .cursor 前缀使 .claude/.agents 会话读 file 字段指向错误目录，且 .cursor 目录一旦缺失即断链。
中性路径在任一平台根下都解析正确（resolve .claude/.agents/.cursor 均 True）。
file 字段仅信息性（流入 Handoff 告知 agent 读哪个文件），无代码 open 它，complete() 只判真值，故安全。
同时：pmem-agent description 从 756 字压到 262；agent 正文 ".cursor/skills/registry.md 核对 heading" 改为平台中性措辞。
test_skill_router 对应断言从 ".cursor/skills/registry.md" 改为 "skills/registry.md"。
