---
name: pmem-learn
description: 当用户输入 /pmem-learn 或 /art-learn，或说「扩展知识/学新技法/补广度」时触发。根据已有域与缺口提出 3~5 条广度扩展（技法卡/风格分叉/相邻模块种子），接受后写入 .memory-art/_knowledge/。
---

# `/pmem-learn`（别名 `/art-learn`）— 【进阶/可选】知识广度 peek

> `finish` 后已**静默 enqueue** 1–2 条建议到 `learn_proposals.json`。本技能用于查看/接受/补提更多。

## 怎么用
```text
/pmem-learn
/art-learn 看看排队的知识卡
```

```bash
python3 pmem_art.py learn suggest          # 大声列出建议（peek）
python3 pmem_art.py learn accept --all
python3 pmem_art.py learn list
```
