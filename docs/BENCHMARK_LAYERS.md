# Benchmark 三层（B1 / B2 / B3）

> **合同**：不要把「记忆文件变多 / CLI 跑通」说成「视觉能力进化了」。  
> 本仓库的 `benchmark_evolution.py`（根目录与 `tests/`）属于 **B1 系统集成测试**，不是视觉实证。

## 对照表

| 层级 | 测什么 | 证明什么 | 本仓库入口 |
| :--- | :--- | :--- | :--- |
| **B1 系统测试** | CLI、记忆落盘、Warm-Start 召回、路由、资产 ingest、评分字段流转 | 管线功能正常 | `benchmark_evolution.py`、`tests/benchmark_evolution.py` |
| **B2 视觉测试** | 真模型出图 + 独立 VLM 盲评；冷启动 vs Warm-Start 对照 | 图片质量是否因记忆变好 | `benchmarks/b2_visual_suite.yaml` + `pyw -3 -u benchmarks/b2_visual_bench.py` |
| **B3 生产测试** | 画师验收、Unity 导入、实机规格 | 商业交付能力 | 人工验收清单（非自动绿灯） |

## B1 能报 / 不能报

**可以报**：modules/entries/recipes/redlines 数量、Warm-Start 命中、红线是否写入、CLI 退出码、会话字段是否落盘。

**禁止报成**：画质提升、角色一致性进化、风格稳了、因为记忆所以更好看。  
B1 使用程序化/示意 PNG + **剧本预设分**时，分数只验证「数据能流转」，与像素无关。

历史旁证：[`benchmark_evolution_agent_vs_vlm.md`](benchmark_evolution_agent_vs_vlm.md) 已显示同一批示意过程图上，剧本分与独立 VLM 盲评可以严重脱钩。

## B2 固定任务集（示意骨架）

见 `benchmarks/b2_visual_suite.yaml`。默认覆盖：

1. 同一角色不同表情  
2. 同一角色不同姿态  
3. 同一场景不同镜头  
4. 同一 UI 家族不同弹窗  
5. 不同等级的合成梯  
6. 原画拆层与重新叠回  

### 建议追踪的真实视觉指标（示意，非仓库实测）

| 指标 | 含义 |
| :--- | :--- |
| 角色一致性 | 同身份跨表情/姿态是否可认作同一人 |
| 风格一致性 | 色板/光影/笔触是否同族 |
| 需求符合度 | 是否满足 brief（表情、机位、档位） |
| 图层还原度 | 拆层叠回后与原图对齐程度 |
| 规格合格率 | 尺寸/透明/安全边/九宫格等硬规格 |

比较方式：**无记忆冷启动** vs **有记忆 Warm-Start**，同一裁判、同一任务 ID；报告均值与退化项，而不是 entries 条数。

## B3

画师点头、引擎导入、上架截图规格。通过标准由项目主美定义；Doctor 不自动宣称 B3 通过。

## Doctor 挂钩

`doctor` 会读取 `.memory-art/_profile/b2_last.json`（若存在）。相对 baseline 任一核心指标掉 ≥ 阈值时记入硬信号「B2 退化」，不替代人工验收。另检查：技能文件是否齐全、candidate 记忆堆积、缺图锚点，并打印修复建议。

## B2 真评流水线（有 VLM Key 时）

```bash
# 1) 对真实成图按任务盲评（写入 .memory-art/_profile/b2_results.jsonl）
pyw -3 -u benchmarks/b2_visual_bench.py --root . --score-image path/to/real.png --task-id b2-char-expr --arm warm_start

# 2) 冷启动对照臂同理（--arm cold_start）

# 3) 汇总为 empirical 报告
pyw -3 -u benchmarks/b2_visual_bench.py --root . --assemble
pyw -3 -u benchmarks/b2_visual_bench.py --root . --assemble-baseline   # 固化基线时

# 4) 退化对比
pyw -3 -u benchmarks/b2_visual_bench.py --root . --compare-baseline
```

无 Key 时不要用 `--allow-agent-fallback` 宣称进化（该开关只测 plumbing，`empirical=false`）。
