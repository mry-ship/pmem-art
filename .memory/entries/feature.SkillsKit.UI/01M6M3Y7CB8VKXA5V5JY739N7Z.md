---
id: 01M6M3Y7CB8VKXA5V5JY739N7Z
module: feature.SkillsKit.UI
entity: UIMultiLens
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/converge.py
- skills_kit/converge_policy.py
- skills_kit/converge_loop.py
- skills_kit/install.py
- skills_kit/skill_registry.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: UI审稿六层；权重反了结构挂，不靠材质交差
verify: skill_specs 含多维透镜；docs/UI_MULTI_LENS.md 存在
applies: /pmem-ui 主菜单概念出图与审图
source:
  conversation: ccfc4c53-773f-4c77-90b0-4088c1330449
---
用户2026-11-05要求把前面踩坑收成 UI 多维总结：用户体验、视觉扫视、颜色构造、整体风格、按钮重要程度、上下方设计。
已写入 skill_specs「主菜单多维透镜」+ docs/UI_MULTI_LENS.md。
要点：先真按钮截图；P0主任务>P1进度>P2资源>P3底栏>P4次入口>P5设置；顶栏单行右上设置；休闲可有底栏Home居中；色服务于层级（70/20/10）；禁keyart冒充HUD、禁权重颠倒靠材质装高级。
