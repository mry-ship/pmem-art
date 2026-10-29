# Absolute-5D 双轨（无独立 VLM Key 时）

> **规范原文**：[`gpt6sol_absolute_5d_quant_rubric.md`](gpt6sol_absolute_5d_quant_rubric.md)  
> **像素实现**：`scripts/absolute_5d_scorer.py`（`v9.1_audit_patch`）— **仅旁证**  
> **无 Key 主路径**：当前能看图的模型按检查表打五维分（`skills_kit/absolute_5d_agent_rubric.py`）

## 双轨（门槛统一）

| 轨 | 何时 | 主分来源 | STOP |
| --- | --- | --- | --- |
| Independent VLM | 有 API Key | `independent_vlm` | ≥**9.60**（档位 profile） |
| Agent Absolute-5D | 无 Key / API 失败 | 本模型看图 + 检查表 → CLI `dims`（`agent_absolute_5d`） | ≥**9.60**；未达标继续；满 `max_rounds` → **best-of-N** |
| Pixel offline | 任意 | 可测代理旁证 | **不设门槛、不早停、不改 accept_threshold** |

**禁止**：无 Key 另设 8.50 硬顶 / 假早停（像素尺软顶≈8.85，与 9.6 无关，拿 8.50 当闸会假达标）。

## 无 Key 怎么评

1. Agent 读 `agent_absolute_5d_judge_prompt()`，对生成图按 Absolute-5D 出 `构图x/光影x/透视x/质感x/风格x` + 可核验 defects。  
2. `converge judge` 吃 CLI dims；加权分与物理闸 / 软缺陷闸同有 Key 路径。  
3. 像素 `absolute_5d` 写入 warning/旁证；**不改 9.60 门槛、不单独早停**。Agent 五维若高于旁证超过 **0.80**，正式分压到 `旁证+0.80`（独立 VLM 不套这顶）。  
4. `<9.6` → `CONTINUE`；满轮 → `STOP_MAX_ROUNDS`，finish 取历史最高分。

## 像素尺还做什么

批量对比、无视觉模型时的粗定位、审计 MAE。弱代理 → N/A；无透视维软顶 8.85 只约束**像素旁证总分诚实性**，不是 converge 合同。

```bash
PYTHONPATH=. python3 scripts/absolute_5d_scorer.py
```
