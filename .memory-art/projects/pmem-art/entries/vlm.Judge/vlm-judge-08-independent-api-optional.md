---
id: vlm-judge-08
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 配置了视觉 API key 则 converge judge 调独立模型；未配置则回退 Agent 自评
---
`vlm_judge.py` 读取 `.memory-art/config.yaml` 的 `vlm_judge:`、可选 `vlm_judge.local.yaml`（gitignore）与环境变量 `PMEM_VLM_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`。`enabled=auto` 且无 key 时 `source=agent_self_judge`。有 key 时覆盖 CLI `--dims`，仍经 `audit_score_inflation` 与物理闸门。`on_error=fallback` 失败回退自评。CLI：`pmem_art.py vlm-judge status|probe`。
