---
name: pmem-learn
description: 当用户输入 /pmem-learn 或 /art-learn，或说「扩展知识/学新技法/补广度」时触发。根据已有域与缺口提出 3~5 条广度扩展（技法卡/风格分叉/相邻模块种子），接受后写入 .memory-art/_knowledge/。
---

# `/pmem-learn`（别名 `/art-learn`）— 知识广度自动扩展

## 怎么用
```text
/pmem-learn
/art-learn 我角色画得多，场景光影词汇不够
扩展知识 / 补广度 / 学新技法
```

## 原理
反馈新词 · 参考图解构 · improve 发现邻域缺口 → 提案 3~5 张知识卡 → 你说「接受」写入 `_knowledge/`（可选空模块种子）→ 下次 warm-start 更博。

```bash
python3 pmem_art.py learn suggest
python3 pmem_art.py learn accept --all
python3 pmem_art.py learn accept --ids tech-watercolor,light-rim
python3 pmem_art.py learn list
```

## 个人进步
广度与深度双轮：converge 加深手艺，learn 拓宽技法库，improve 固化口味。
