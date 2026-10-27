---
name: pmem-coach
description: 玩家要看进步、口味、短板练习或知识卡时使用。只有 /pmem-coach 这一条。日常 converge finish 已经在后台写过，不要主动推销。知识卡没有玩家明确说收下，就不要写入。
---

# `/pmem-coach` — 进步 / 短板 / 知识（三条偷看合成一条）

日常 `converge finish` 已经在后台写过反思、口味和知识队列。只有玩家来要报告时才跑。一次只出一份，不要把三份一起倒出来。

看玩家这句话里要哪一份。没点明就只出短板。

| 玩家在说 | 跑 |
| :--- | :--- |
| 总结、进步、口味 | 进步 |
| 知识、技法、广度 | 知识 |
| 短板、练习、练什么，或没点明 | 短板 |

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
