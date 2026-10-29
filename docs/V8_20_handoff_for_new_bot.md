# V8→V2 · 20 bot 批跑交接

规则完全跟仓库 `skills_kit/` 走（`prompt_scale.py`、`converge.py`）。中文沟通。工作区：`/Users/yanghu/Desktop/pmem-art/`。

## 合同参数

| 项 | 值 |
|---|---|
| 停分 `DEFAULT_THRESHOLD` | **≥ 9.50** |
| 最大轮次 `DEFAULT_MAX_ROUNDS` | **8** |
| low / medium 最早可停 | 满 **1** 轮且 ≥9.50 |
| high / recompose（含 bold）最早可停 | 满 **2** 轮且 ≥9.50 |
| 四档 `max_rounds` | 均为 **8** |

达标：`score ≥ 9.50`，且已满该档 `min_rounds_before_stop`，且 skill 闸门/意图通过 → `STOP_TARGET_REACHED`；否则继续生成直到第 8 轮。

## 跑这 20 个

4 风格 × `low_best` / `medium_best` / `high_best` / `recompose` / `recompose_bold`：

- v8_bot_02
- v8_bot_04
- v8_bot_06
- v8_bot_07
- v8_bot_08
- v8_bot_10
- v8_bot_12
- v8_bot_14
- v8_bot_15
- v8_bot_16
- v8_bot_18
- v8_bot_20
- v8_bot_22
- v8_bot_23
- v8_bot_24
- v8_bot_26
- v8_bot_28
- v8_bot_30
- v8_bot_31
- v8_bot_32

- 任务表：`bot_tasks_v8.json`
- 最优方向：`best_prompts_by_scale.json`
- 档位指令与权重：`skills_kit/prompt_scale.py` → `CONVERGE_SCALE_PROFILES`

原图（同尺打分，进 HTML）：

- `style_ref_01_night_city.png`
- `style_ref_02_pastel_sketch.png`
- `style_ref_03_sunlit_portrait.png`
- `web_ref_01_concept_ishtar.png`

## 执行步骤

1. 用项目 converge（`pmem_art` / `skills_kit.converge`）按上表参数跑每个 bot。  
2. 对 style ref 从零出图；按档位套 profile（low 微修、medium 光影、high 戏剧叙事点缀、recompose 新机位、bold `style_jump`）。  
3. 每轮打 Absolute-5D（或项目 VLM judge）→ 写缺陷 → 回流成下一轮新 prompt → 整图再生成。  
4. 保存终图、`_r1`…`_rK`、manifest（轮次、分数、停因）。  
5. 输出目录建议：`generated_v8_20_skill/`。

## 评分与 HTML

- 评：4 原图 + 20 终图 + 全部中间轮；达标统计按 **≥9.50**。  
- HTML：版式对齐 `pmem_art_images_v6_32bots_showcase.html`，产出 `pmem_art_images_v8_20bots_showcase.html`（`pmem-art/` 与桌面根目录）。  
- 页内：汇总（均值、≥9.50 张数、轮次分布）、原图区、20 卡（分/五维/轮次/停因/缺陷）、分风格小计；相对路径离线可开。

## 验收

- 20 张新图齐全  
- 停分 9.50、上限 8 轮，行为与 `skills_kit` 一致  
- 原图已评分并进页  
- HTML 为 v6 showcase 风格，轮次可见  
- 报告含达标数、未达标列表与停因  

## 路径

```
/Users/yanghu/Desktop/pmem-art/
  skills_kit/prompt_scale.py
  skills_kit/converge.py
  pmem_art.py
  bot_tasks_v8.json
  best_prompts_by_scale.json
```
