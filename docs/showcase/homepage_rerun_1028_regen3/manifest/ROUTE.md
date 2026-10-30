# regen3 路由与步骤（总控）

banner: 【按 普通图、UI、Mode A、Mode C、合成梯 走了】（showcase 命中）
本趟默认同范围补齐：克隆、变体、锁风格、提示词（旧页有，`_showcase_ids` 探针未覆盖）
输出：docs/showcase/homepage_rerun_1028_regen3/
源：docs/showcase/homepage_rerun_1028/index.html

并行窗口：
- draw c01 / c02 / c03 / c04
- ui royal
- icon A+C
- clone+variant
- merge
- style+prompt

## 收尾硬要求（玩家 2026-10-30）
跑完后反向分析 → **有问题的全部修复**（路由/技能文案/阈值/展陈门禁/探针缺口等），不要只交问题清单。

## 修复后验收（玩家 2026-10-30）
改完技能/路由/闭环后必须详细检查：逻辑无误、运行正常。
最低回归：相关 unittest + `pmem_art.py route` 展陈同范围样例 + `showcase-gate` + 至少一条 converge 短路径烟雾。

- UI royal: concept max 8.96 / sheets max 9.01 — 满4轮未过9.5（记入反向修复）

- c01 四档均未过9.5（low/med 8.84；high 8.62 灯笼叙事漂手提；recompose 8.49 前两轮未换机位）→ 反向修复

- c03: low 9.45 差一线；medium/high/recompose 均≥9.51 达标

- c02 四档均未过9.5（最高 high 9.34 / recompose 9.33）；双手撑地与侧收腿贴参考是主短板

- icon A 三枚均≥9.50；heal 关键枚满轮最高9.40未过线；其余C同套一次出

- c04 四档均未过9.5（med/high 9.46；recompose 最高仅8.62，平视向下未立住）；finish 会 ingest 到 assets/scene — 记入反向修复
