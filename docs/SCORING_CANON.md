# 评分规范真源（Canonical）

> **唯一对外真源**：本文 + 实现 `skills_kit`（`parse_5d_dims` / `converge_policy`）+ `vlm_judge.py`。  
> README / Skill / ARCHITECTURE 若冲突，以本文与代码为准；发现漂移请改文档，不要再分叉一套尺。

## 1. 呈现维：六维（正式尺）

| 键 | 中文 | 角色 |
| :--- | :--- | :--- |
| `composition` | 构图 | 工艺维 |
| `lighting_color` | 光影色彩 | 工艺维 |
| `perspective_anatomy` | 透视与解剖 | 工艺维（角色硬门槛常挂此维） |
| `texture_detail` | 质感 | 工艺维 |
| `spec_style` | 规格与风格 | 工艺维 |
| `flawlessness` | 无瑕度 / 无瑕疵 | **固定约 25%**；盲评，缺维不能停 |

**总分**：六维加权**调和平均**（不要手填总分）。无瑕度固定 25%，其余五维按媒介家族分配（见 `get_converge_scale_profile` / 家族权重表）。

**停机线**：正式分 ≥ **9.50**（且过硬门槛与物理图闸）。

## 2. Absolute-5D 是什么

**Absolute-5D** = 上表前五个工艺维的历史别名（构图/光影/透视解剖/质感/风格）。

| 说法 | 实际含义 |
| :--- | :--- |
| Absolute-5D / `parse_5d_dims` | API/函数名残留；有 `flawlessness` 时按**六维**算；缺无瑕度时退回工艺五维（日常交件禁止缺无瑕度） |
| Agent Absolute-5D 检查表 | 无独立 VLM Key 时，Agent 按同一六维合同看图填分 |
| 展陈旧文「主闸 Absolute-5D」 | 过时措辞；现行正式呈现与停机一律按**六维** |

`vlm_judge.build_judge_system_prompt`：五维 craft 权重归一后各 ×0.75，再加无瑕度 25%，要求模型输出六个数。

## 3. 硬性否决（摘要）

细则在 `skills_kit/converge_policy.py` 与 [RULES_AND_RUBRIC.md](RULES_AND_RUBRIC.md)。要点：

- 人物/动物/机械：透视解剖 &lt; 7.5 → 正式分改取该维，不能停（缺维 fail-closed）
- 场景结构塌缩线等媒介特例见 policy
- UI / 图标 A·B·C：各有专用维名与门槛（展示仍可带无瑕度）
- 管线合规可旁记，**默认不进**六维乘积
- 缺陷空话 / 虚高审计 / 占位图 → 不得 `STOP_TARGET`

## 4. 不同交付类型

| 交付 | 评分体系 |
| :--- | :--- |
| 普通图 / 原画 / 克隆 / 变体 / 镜头包 | 标准六维 + 媒介家族权重 |
| UI | 结构等专用维 + 无瑕度；管线合规旁记 |
| 图标 A / B / C | 各档专用维（见 `/pmem-icon`）；勿与插画六维混填 |
| 合成梯 | 整表/逐格仍走 converge 六维合同；关系论述另闸 |

## 5. 与 Benchmark 的关系

- **B1**：可灌预设分，只测流转 → **不能**当视觉进化证据  
- **B2**：必须真图 + 独立 VLM（或主美盲评）按本文六维/专用维打分  

记忆晋升与配方可信度见 [MEMORY_TRUST.md](MEMORY_TRUST.md)。
