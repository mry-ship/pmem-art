# `/pmem-coach` 展陈偷看报告

**【按 coach.report 走了】** · session `showcase-coach-20261123` · 知识卡仅列出建议，**未**执行 `learn accept`。

---

## 一、进步（improve + progress + taste）

### 自我迭代 peek（`improve run`）

- 扫描反思会话：**20** 份（最近 20）
- 近期平均胜出分：**9.08**
- 近期平均收敛轮次：**3.35**
- 高频翻车点（节选）：UI 状态族 Pressed 未压暗内陷、九宫格套件多态不足；merge 场景发生器身份/情人节题材漂移；NPC 装扮与道具语义错位等
- 口味档案：本次无新增短语（信号不足或已收敛）
- 强化优先 recipe（warm-start 加权节选）：`icon.AppIcon` 圣诞 1024 母版多条 9.60+；`brand.WorldStyle` 多图分工卧室机位 9.61

### 进步曲线（`progress`）

| 窗口 | n | 平均胜出分 | 平均轮次 | 达标率 |
| :--- | ---: | ---: | ---: | ---: |
| 最近 7 次 | 7 | 8.87 | 2.86 | 0.14 |
| 最近 30 次 | 30 | 9.07 | 3.47 | 0.17 |

- 口味信号：keeps=7 · rejects=27 · style_fixes=62 · sessions=20
- 偏好：光影=柔光/暖光/顶光；构图=全身/居中/对称/半身
- 禁用习惯（节选）：过曝高光、漏抠毛边、赛博霓虹、狗狗棋子只画狗头/黑珠眼等
- 短板趋势：**↓变强** style_lock、material；**↑需练** lighting、narrative_camera、line_edge、color_palette、composition、anatomy
- 知识广度：项目私有 **8** 张卡片

### 口味档案快照（`taste show`）

- 档案：`.memory-art/_profile/taste.json`（updated 2026-11-23）
- `preferred_lighting`：柔光、顶光、暖光
- `preferred_composition`：全身、居中/对称构图、半身
- `preferred_color_temperature`：暖色调、避免过饱和
- `keep_phrases`：merge 五链升级、妖精花园/海鲜货柜/花瓣蘑菇等正向锚点（见 CLI 全文）
- `reject_phrases`：样张偏离、货柜气质、狗狗棋子规范等红线句库

---

## 二、短板与练习（`coach` + `progress` 交叉）

**扫描反思：20 份**

| 排序 | 短板 | 命中 | 练习方向 |
| ---: | :--- | ---: | :--- |
| 1 | lighting | 70 | 固定机位顶光/侧逆光/黄金时刻对比；只改光源重绘 |
| 2 | narrative_camera | 52 | 远/中/特写三景别；Key Art 先叙事再构图 |
| 3 | line_edge | 50 | 透明底 200% 查毛边；统一描边预设重描 |
| 4 | color_palette | 34 | 模块 palette 限 3 HEX；脏色/霓虹写 Negative |
| 5 | material | 29 | 同形金属/布/陶瓷；去油腻高光改釉面分层 |

**下一张建议练：** lighting → narrative_camera → line_edge（详见 `.memory-art/_profile/coach_plan.json`）

**趋势：** 短板下降 composition、narrative_camera；上升 line_edge、color_palette

---

## 三、知识广度偷看（`learn suggest` + `learn list`，未写入）

### 待选建议（仅暂存 `learn_proposals.json`）

1. `key-extreme-breakdown` — 动画运动规律：关键帧-极端帧-中分帧与预备缓冲（缺 anim 域卡片）
2. `palette-70-20-10` — 色彩构成：70-20-10 色板比例（缺 brand 域卡片）
3. `material-surface-physics` — 材质：金属/织物/陶瓷高光区分
4. `anatomy-head-ratio` — 头身比尺规与重心
5. `eye-hierarchy` — 五官主次与第一识别锚点

> 玩家明确「收下/写入」后才可 `learn accept`；本次展陈 **禁止自动 accept**。

### 现有图谱

- **项目私有** 8 张：cam-cinematic、light-rim、style-chibi、tech-9slice、tech-celshade、tech-painterly、tech-pixel、tech-watercolor
- **跨项目共享** 15 张：含 golden-hour-scene、composition-thirds-grid、palette-70-20-10（部分已在共享层，与 suggest 缺口对照可见）

---

## CLI 原始落盘（审计）

| 命令 | 文件 |
| :--- | :--- |
| `coach` | `_coach.txt` |
| `improve run` | `_improve_retry.txt`（首轮因档案锁失败见 `_improve.txt`） |
| `progress` | `_progress.txt` |
| `taste show` | `_taste.txt` |
| `learn suggest` | `_learn_suggest.txt` |
| `learn list` | `_learn_list.txt` |