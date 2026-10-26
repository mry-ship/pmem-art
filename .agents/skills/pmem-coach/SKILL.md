---
name: pmem-coach
description: 当用户输入 /pmem-coach 或 /art-coach，或说「练什么/我的短板/能力提升计划」时触发。把红线与会话反思归类为构图/光影/解剖/九宫格等能力维，输出个人练习计划与下一张绘制目标。
---

# `/pmem-coach`（别名 `/art-coach`）— 【进阶/可选】能力教练 peek

> 日常收敛只会给一行「小提示」。本技能用于你**主动要练习计划**时。

## 怎么用
```text
/pmem-coach
/art-coach 我最近老是翻车，给我练习计划
```

## 原理
红线 + `_reflections/` → 短板类别 → drills → `next_draw_goals`。

```bash
python3 pmem_art.py coach
python3 pmem_art.py progress
```
