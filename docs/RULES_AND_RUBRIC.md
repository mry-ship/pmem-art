# pmem-art 规则手册、五维审图标准与收敛强度 (Scale) 规范

> 本文档收纳 `pmem-art` 完整的**双层记忆架构规范**、**五维自评收敛权重**、**`--scale` 低/中/高/改构图四档收敛强度机制**以及 **CLI / Skill 调用手册**（主仓库首页 `README.md` 保持精简看图模式）。

---

## 1. 双层记忆架构与最多四层模块硬顶 (`MAX_MODULE_DEPTH = 4`)

| 层级 | 路径 | 职责与隔离边界 | 排序权重 (`rank_score`) |
| :--- | :--- | :--- | :--- |
| **Layer 1 · 项目专项记忆层** | `<project>/.memory-art/projects/<project-slug>/` | 严格隔离当前项目的模块树（最多 4 层：`L1.L2.L3.L4`）、项目红线 (`redlines`)、审美偏好 (`taste`)、风格圣经 (`style-bible`) 与收敛日志 (`converge/*.json`)。复制 `.memory-art` 到新项目时自动新建独立专项库并保留历史项目。 | 项目私有优先 (`+0.35` project boost) |
| **Layer 2 · 全局基础工艺层** | `~/.pmem-art/shared/` | 仅存放跨项目通用的 14 张底层美术工艺卡片（如：**70-20-10 色彩比例**、**45° 侧逆光轮廓分离**、**次表面散射 SSS**、**300g 冷压粗纹纸飞白肌理**、**近中远三层大气透视**、**五指与关节解剖红线**）。新项目冷启动自动挂载。 | 低于项目专项层 (`base_weight * 0.75`) |

---

## 2. 收敛强度参数 (`--scale low|medium|high|recompose`) 内部机制

在 `pmem_art.py converge` 与 `/pmem-draw` 中，支持通过 `--scale` 与 `--recompose-dir` 控制收敛幅度：

```bash
# 1) 低强度（只修缺陷，锁死原图机位/姿态/元素数量）
python3 pmem_art.py converge start --session s_low --scale low --goal "..." --ref-image ref.png

# 2) 中强度（默认：保持构图框架，补足光影层次与材质微肌理）
python3 pmem_art.py converge start --session s_med --scale medium --goal "..." --ref-image ref.png

# 3) 高强度（Showcase级：允许大胆重构镜头张力、重做戏剧化光影与叙事细节）
python3 pmem_art.py converge start --session s_high --scale high --goal "..." --ref-image ref.png

# 4) 定向改构图模式（按用户明确指令改变机位/景别/主体位置，100%保留画风基因）
python3 pmem_art.py converge start --session s_rec --scale recompose \
  --recompose-dir "从胸像正面特写改为复古阳光植物画室全景构图，主体移至右侧三分点" \
  --goal "..." --ref-image ref.png
```

### 四档 Scale 内部参数表 (`CONVERGE_SCALE_PROFILES`)

| Scale 档位 | 定位 | 五维权重分配 (`构图 / 光影 / 透视解剖 / 质感 / 规格风格`) | `next_fix` 改动预算 (`max_prompt_delta_ratio`) | 允许重构构图 (`allow_recompose`) | 允许重做光影 (`allow_lighting_overhaul`) | 单轮最低跃升目标 (`min_round_leap`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`low` (低强度)** | 只修解剖/杂色/纸纹缺失，严禁增删配饰或改机位 | `15% / 20% / 25% / 25% / 15%` | `<= 20%` (保守修补) | `False` | `False` | `+0.15` |
| **`medium` (中强度·默认)** | 保持原构图框架，补足轮廓光、SSS 与材质颗粒 | `20% / 25% / 20% / 20% / 15%` | `25% – 45%` (均衡优化) | `False` | `True` | `+0.35` |
| **`high` (高强度)** | 允许重构镜头机位、戏剧化光影（木漏日/丁达尔光）与前景压角 | `25% / 30% / 15% / 20% / 10%` | `50% – 80%` (大胆跃升) | `True` | `True` | `+0.55` |
| **`recompose` (定向改构图)** | 100% 执行用户指定的新构图方向（如特写改全景/主体移位），锁死原画风 | `30% / 25% / 20% / 15% / 10%` | `60% – 85%` (定向重构) | `True` | `True` | `+0.50` |

---

## 3. 五维严苛审图标准与反虚高机制 (Anti-Inflation Rubric)

针对早期审图中曾出现的「因未乱加配饰/基本完成度达标而给分偏高（如 Case 02 R2 曾虚高至 9.65 分，实际严苛重审为 8.80 分）」问题，五维审图强制执行以下**严苛扣分准则**：

1. **构图与视觉张力 (`Composition`, 15%–30%)**：
   - 若仅平庸照搬参考图的呆板居中/证件照裁切、缺乏前景压角或明度重心锚点，**最高不超过 8.6 分**。
2. **光影与色彩层次 (`Lighting & Color`, 20%–30%)**：
   - 必须具备明确的 `70-20-10` 冷暖主辅色比例与主光/轮廓光/环境反射光三层分离；平光或简单一刀切二分阴影**最高不超过 8.8 分**。
3. **透视与解剖结构 (`Perspective & Anatomy`, 15%–25%)**：
   - 严格检查五指关节、鞋带透视、建筑消失点与近中远三层空气透视。
4. **物理媒介质感 (`Texture & Material Authenticity`, 15%–25%)**：
   - 严禁将「数字噪点滤镜」误判为真实纸纹！例如 300g 冷压粗纹纸油画棒必须看见**未填满的纸纹凹槽飞白（Unpainted Paper Tooth Gaps）**与**厚涂蜡质笔触（Dry Impasto）**；若涂色过于均匀死板，质感项直接扣至 **8.8 分以下**。
5. **规格与风格完成度 (`Spec & Style`, 10%–15%)**：
   - 仅作为基础底线项，防止「不出错即高分」掩盖画面冲击力与质感短板。
