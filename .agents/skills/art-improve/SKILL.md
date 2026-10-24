---
name: art-improve
description: 当用户说「提升/自我迭代/总结这次/越用越好」或输入 /pmem-improve /art-improve 时触发。扫描会话反思与反馈红线，更新个人口味档案 taste.json，并汇报进步曲线。
---

# `/pmem-improve`（别名 `/art-improve`）— 连续自我迭代

## 怎么用（复制即用）
```text
/pmem-improve
/art-improve 总结最近几次，看看我哪里变强了
提升一下 / 自我迭代 / 越用越好
```

## 原理（截图摘要）
1. 每次 `converge finish --apply` 已自动写会话反思 → 2. 本技能扫描反思+反馈+红线 → 3. 更新 `.memory-art/_profile/taste.json` → 4. 打印进步曲线与「变聪明了什么」

## 个人进步
系统会汇总近 7/30 次胜出分、收敛轮次、高频红线，并降低重复短板——**越用越好**。

### 标准命令
```bash
python3 pmem_art.py improve run          # 自我迭代（更新口味档案）
python3 pmem_art.py progress             # 进步曲线
python3 pmem_art.py taste show           # 查看口味档案
python3 pmem_art.py coach                # 能力教练计划（弱项→练习→下一张目标）
```

向用户用中文汇报：扫描了多少反思、口味新增了什么、短板是否在下降。
