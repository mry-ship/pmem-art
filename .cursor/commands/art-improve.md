---
description: 【进阶/可选】进步、短板与知识卡（日常已静默写过）（pmem-art）
---

> **点名锁定**：玩家用了 `/art-improve`，类型固定为 **进步**。不要改判，不要改问。下面只执行这一支。

# `/pmem-coach` — 进步 / 短板 / 知识（三条偷看合成一条）

日常 `converge finish` 已经在后台写过反思、口味和知识队列。只有玩家来要报告时才跑。一次只出一份，不要把三份一起倒出来。

文件开头若写着「点名锁定」，就按锁定的那一支。否则看用词：

| 玩家在说 | 跑 |
| :--- | :--- |
| `/pmem-improve`、`/art-improve`、总结、进步、口味 | 进步 |
| `/pmem-learn`、`/art-learn`、知识、技法、广度 | 知识 |
| `/pmem-coach`、`/art-coach`、短板、练习、练什么，或没点明 | 短板 |

## 进步
```bash
python3 pmem_art.py improve run
python3 pmem_art.py progress
python3 pmem_art.py taste show
```

## 短板
```bash
python3 pmem_art.py coach
python3 pmem_art.py progress
```
红线加会话反思，收成构图、光影、解剖、九宫格等短板，给下一张该练什么。

## 知识
```bash
python3 pmem_art.py learn suggest
python3 pmem_art.py learn list
```
只列出建议。玩家明确说「收下」或「写入」之后，才运行 `python3 pmem_art.py learn accept`。禁止自动 `accept --all`。
