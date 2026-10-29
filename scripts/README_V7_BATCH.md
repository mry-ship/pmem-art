# V7 批跑说明（松闸后任务层）

## 权威代码

```text
/Users/yanghu/Desktop/pmem-art/
```

批跑必须加载 **Desktop `skills_kit/` 包**，不要再用旧单体 `skills_kit.py`。

```bash
cd /Users/yanghu/Desktop/pmem-art
export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
python3 -c "import skills_kit, inspect; print(skills_kit.__file__)"
# 期望: .../pmem-art/skills_kit/__init__.py
```

## 产物

| 文件 | 作用 |
| :--- | :--- |
| `bot_tasks_v7.json` | 32 bots；无「严格保留DNA / 垫图一致性高 / 构图：锁死」；high goal 写 50–80% |
| `best_prompts_by_scale.json` | 按档最优方向（加法，非第二份锁） |
| `scripts/v7_image_scorer.py` | high/recompose/bold 的 struct 权重=0；**无** `struct>0.35→≥9.50` |
| `scripts/run_32bots_v7_dry.py` | **不出图** dry-run：preflight + 剥锁 + `min_rounds≥2` |

## 自检

```bash
cd /Users/yanghu/Desktop/pmem-art
python3 pmem_art.py check-scale-gates --self-check
PYTHONPATH=. python3 scripts/run_32bots_v7_dry.py
PYTHONPATH=. python3 scripts/v7_image_scorer.py
rg -n '严格保留DNA|参考垫图一致性高|构图：锁死' bot_tasks_v7.json best_prompts_by_scale.json
rg -n '≤60%' bot_tasks_v7.json
rg -n 'struct\s*>\s*0\.35' scripts/*scorer*.py
rg -n 'min_rounds' scripts/run_*v7*.py
```

## 真正出图时

接 Desktop `converge start/generate/judge`；`high`/`recompose`/`recompose_bold` 必须走引擎 `min_rounds_before_stop`（≥2），禁止仅凭外挂 scorer ≥9.50 在 R1 STOP。
