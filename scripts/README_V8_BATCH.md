# V8 批跑说明（Absolute-5D v9.1 离线检查项 + V2 展陈密度）

## 权威代码

```text
/Users/yanghu/Desktop/pmem-art/
```

```bash
cd /Users/yanghu/Desktop/pmem-art
export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
python3 -c "import skills_kit; print(skills_kit.__file__)"
```

## 产物

| 文件 | 作用 |
| :--- | :--- |
| `scripts/absolute_5d_scorer.py` | **像素旁证 v9.1**（弱代理 N/A）；有 Key→VLM；无 Key→Agent Absolute-5D@9.5，本尺不设早停 |
| `docs/gpt6sol_absolute_5d_quant_rubric.md` | 规范原文（可量化分析） |
| `docs/OFFLINE_ABSOLUTE_5D.md` | 无 Key 落地说明 |
| `docs/offline_vs_vlm_gap_gpt6sol_audit.md` | gpt-6-sol 分差审计 |
| `bot_tasks_v8.json` | 32 bots；夜城 recompose=乌篷仰桥；bold 拆开；无 DNA 锁词 |
| `best_prompts_by_scale.json` | 按档加法 |
| `scripts/run_32bots_v8_dry.py` | 不出图 dry-run |
| `scripts/run_32bots_v8_live.py` | **必须** `--score-only` 或 `--converge`；禁止假多轮复用终图。脚本内 8.50 仅为像素旁证诊断带，**≠** 产品 converge 合格线 9.50 |
| `scripts/v7_image_scorer.py` | 诊断 only |

## 量程锚点（v9.1 audit-patched）

对齐 `docs/gpt6sol_absolute_5d_quant_rubric.md` + 审计补丁：弱语义代理 **N/A**；可测项 0/1/2；缺项向先验 **7.0** 轻收缩。

| 锚点 | 目标分 |
| :--- | :--- |
| 废图 / 极糊缩略图 | ≤4.5 |
| 软糊概念板（夜城 405×720） | ~6.5–8.2（分辨率不硬封顶质感） |
| 可用 / 强展陈 | ~7.5–8.8 |
| near-perfect 档位语言（旁证） | ≥**8.50**（非 converge 闸） |

- **有 VLM Key → 主分走 VLM@9.5**；无 Key → `agent_absolute_5d`@**9.5**（满轮 best-of-N）；像素离线仅旁证。
- Legacy **9.50** 不绑离线。
- Intent/Δ 仍是诊断，不是语义。

## 重要限制

1. `--score-only` **不调用 GenerateImage**，也不证明 V8 提示追上 V2。
2. `min_rounds≥2` 时缺 `*_rN` 中间图 → **FAIL**（禁止复用终图冒充多轮）。
3. 验收 dry：`python3 scripts/run_32bots_v8_dry.py` → 32/32 OK。
4. 离线尺自检：`python3 scripts/absolute_5d_scorer.py`。
