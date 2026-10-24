---
name: pmem-improve
description: 当用户说「提升/自我迭代/总结这次/越用越好」或输入 /pmem-improve /art-improve 时触发。扫描会话反思与反馈红线，更新个人口味档案 taste.json，并汇报进步曲线。
---

# `/pmem-improve`（别名 `/art-improve`）— 【进阶/可选】自我迭代 peek

> **日常不用喊这个。** `converge finish` / 高信号 `feedback` 后系统已**静默自动驾驶**：写反思、更新口味、强化配方、排队知识建议，最多一行「小提示」。

## 什么时候用
想**主动偷看**进步曲线、口味档案变了什么时：
```text
/pmem-improve
/art-improve 总结最近几次，看看我哪里变强了
```

## 原理
`finish --apply` → 反思 JSON + silent autopilot → taste.json；本技能只是把后台已经做过的事**大声读一遍**。

```bash
python3 pmem_art.py improve run          # 完整报告（peek）
python3 pmem_art.py progress             # 进步曲线
python3 pmem_art.py taste show
python3 pmem_art.py coach                # 能力教练（进阶）
```
