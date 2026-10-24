---
description: 能力教练：短板分类→练习钻→下一张可画目标（pmem-art）
---

# `/pmem-coach`（别名 `/art-coach`）— 个人能力教练

## 怎么用
```text
/pmem-coach
/art-coach 我最近老是翻车，给我练习计划
练什么 / 我的短板 / 能力提升
```

## 原理
红线 + `_reflections/` → 短板类别计数 → 配套 drills → `next_draw_goals`；进步看短板类别是否随时间下降（不只看分数）。

```bash
python3 pmem_art.py coach
python3 pmem_art.py progress   # 含能力短板趋势
```

每轮 converge/critique 后 Agent 还应输出 **「本轮可学」** 1~3 条（与缺陷/修正绑定的具体手艺课）。
