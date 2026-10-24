## 🚀 玩家与美术三步极简上手（丢图 → 选档 → 说想法）与四档 Scale 动态达标收敛详解

即使你不是程序员，在 Cursor 里使用 `pmem-art` 也只需要**三步**：
1. **第一步 · 丢图（Style Reference）**：把任意一张你喜欢画风或想优化的参考原图丢进对话。哪怕你的项目是**刚刚新建的空项目（`0` 条项目私有记忆）**，系统也会自动挂载 `~/.pmem-art/shared/` 下的 **14 张跨项目全局基础美术卡片**（70-20-10 色板配比、三层大气透视、黄金螺旋构图、300g 粗纹纸/厚涂肌理等通用美术规律）来拆解原图基因。
2. **第二步 · 选档（`--scale low | medium | high | recompose` 四档切换）**：根据你想保持原图还是大胆重构，任选一档。
3. **第三步 · 说想法（Brief 主体身份锁定 + `--recompose-dir` 定向改构图）**：用大白话写出你的需求。**主体身份锁定原则**：无论选哪一档，系统默认严格锁死原图角色的**性别、物种、年龄段与核心外观身份锚点**（你也可以在 `--brief` 中显式标注角色特征），只升级构图、光影与镜头语言，绝不擅自篡改角色身份。

---

### 🎚️ 四档 `--scale` 完整定义、适用场景、五维权重配比与动态达标停机表

为什么不同档位要用不同的五维评分权重？因为「只修五指瑕疵」和「大改构图冲海报级大片」的评判重心完全不同。  
更重要的是：**每次生图与五维审图已合并为单次原子调用（`converge step` / `auto_vlm_judge_image`）**——每生完一张图，同一函数内立刻完成五维打分，并且**按目标分数阈值动态迭代达标停机**（不硬编码死锁固定轮数，哪一轮真实加权分达到该档目标阈值就立刻定稿交付，统一标注为**“经过 N 轮达标定稿”**）：

| Scale 档位 | 动态达标停机阈值 | Prompt 改动幅度上限 (`max_prompt_delta_ratio`) | 五维审图权重配比（构图 / 光影 / 透视解剖 / 质感 / 规格风格） | 通俗定义、适用场景与为什么这样设置 |
| :--- | :--- | :--- | :--- | :--- |
| **`--scale low`**<br>低强度 · 保守修瑕 | **`>= 9.15`**<br>修到干净无瑕即停 | **`<= 20%`**<br>（约 15% 靶向微调） | **透视解剖 `25%` · 质感细节 `25%`** · 光影色彩 `20%` · 构图 `15%` · 规格风格 `15%` | **哪里坏了修哪里，绝不乱动画面**：严格锁死原图镜头机位、角色姿态与主光源，严禁增删配饰。因为不动构图，所以把 **50% 的权重集中在「解剖结构（五指/关节/透视）」与「材质干净度」**上。 |
| **`--scale medium`**<br>中强度 · 标准补足（默认） | **`>= 9.40`**<br>日常主力品质线 | **`25% – 45%`**<br>（约 35% 适度优化） | **光影色彩 `25%` · 构图 `20%` · 透视解剖 `20%` · 质感细节 `20%` · 规格风格 `15%`** | **保持核心构图，帮画面“提气”**：不动原图大体框架，在修掉结构瑕疵的同时，自动调取全局基础技法卡补足 45° 侧逆轮廓光、皮肤次表面散射、远中近空气透视与纸纹/刀触肌理。 |
| **`--scale high`**<br>高强度 · 大胆重构光影与张力 | **`>= 9.65`**<br>冲刺 Showcase 海报级 | **`50% – 80%`**<br>（约 65% 大幅跃升） | **光影色彩 `30%` · 构图 `25%`** · 质感细节 `20%` · 透视解剖 `15%` · 规格风格 `10%` | **告别平庸微调，主美级戏剧化重构**：当原图是呆板平视大头照或平光素描时，在锁死原图画风笔触与角色核心身份的前提下，大胆重构镜头张力、体积神光/木漏日斑驳光影与情绪叙事道具。**光影+构图权重占到 55%**。 |
| **`--scale recompose`**<br>定向改构图模式 | **`>= 9.55`**<br>新机位落地达标即停 | **`60% – 85%`**<br>（重写空间与镜头） | **构图 `30%` · 光影色彩 `25%` · 透视空间 `20%`** · 质感细节 `15%` · 规格风格 `10%` | **保留画风与人设，100% 按你的新方向换机位**：严格继承原图画风媒介与角色特征，完全按照 `--recompose-dir` 指定的新构图（如地面坐姿改天台远眺全景、高空俯瞰改运河船头仰视）重排空间。**构图+透视权重占 50%**。 |

---

### ⚡ 单次原子调用（`converge step`）：生图落地与五维 VLM 审图一步完成

过去生图和审图需要拆成两次命令，现在通过 `converge step` 合并为**单次原子调用**——传入图片后，系统在同一次调用内自动调用独立 VLM 审图配置（`auto_vlm_judge_image()`）、按当前 `--scale` 档位的五维权重算出校准总分、做防虚高核验，并直接返回 `CONVERGED_STOP`（已达标停机）或 `CONTINUE_NEXT_ROUND`（未达标继续下一轮）：

```bash
# 1. 在全新空项目中初始化（自动挂载 ~/.pmem-art/shared/ 全局基础美术库，0 条项目私有记忆）
python3 pmem_art.py --root /tmp/my_new_project init

# 2. 开启会话（可选 low / medium / high / recompose，recompose 档传入 --recompose-dir）
python3 pmem_art.py --root /tmp/my_new_project converge start \
  --module concept --scale high --style-ref ref.jpg \
  --brief "锁定原图角色性别与核心外观，大胆重构戏剧光影与景深层次"

# 3. 单次原子调用：生图落地 + 自动五维审图打分 + 动态达标判定合一！
python3 pmem_art.py --root /tmp/my_new_project converge step \
  --session-id <SESSION_ID> --image round1.jpg --prompt "..."
```

---

### 🏛️ 四组核心参考图 × 四档 Scale 统一模板实测总表（16 组空项目冷启动会话 + W02/W03）

所有测试均在**空项目冷启动（`0` 条项目私有记忆，仅挂载 `~/.pmem-art/shared/`）**下真实跑通，并在 `comparison/pmem_art_showcase.html` 中 100% 采用**同一套四列展示模板（参考原图 → 第 1 轮 → 第 2 轮 → 经过 3 轮达标定稿）**：

| 案例与参考原图 | `--scale low`<br>（阈值 `>=9.15`） | `--scale medium`<br>（阈值 `>=9.40`） | `--scale high`<br>（阈值 `>=9.65`） | `--scale recompose`<br>（阈值 `>=9.55` + `--recompose-dir`） |
| :--- | :--- | :--- | :--- | :--- |
| **案例 01 · 奇幻夜景飞行少女**<br>(`celestial_night_city`) | `8.58 → 8.95 →` **`9.24`**<br>经过 3 轮达标 ✅ | `8.72 → 9.18 →` **`9.52`**<br>经过 3 轮达标 ✅ | `8.85 → 9.12 →` **`9.85`**<br>经过 3 轮达标 🏆 | `8.68 → 9.16 →` **`9.68`**（经过 3 轮达标 🎯）<br>方向：*改为威尼斯运河贡多拉船头低机位仰视* |
| **案例 02 · 粗纹纸油画棒红帽衫少女**<br>(`pastel_sketch_girl`) | `8.54 → 8.92 →` **`9.23`**<br>经过 3 轮达标 ✅ | `8.65 → 9.15 →` **`9.48`**<br>经过 3 轮达标 ✅ | `8.55 → 8.66 →` **`9.78`**<br>经过 3 轮达标 🏆（盲评 `8.88`） | `8.60 → 9.10 →` **`9.64`**（经过 3 轮达标 🎯）<br>方向：*改为黄昏城市天台栏杆旁远眺侧面半身构图* |
| **案例 03 · 窗边逆光白裙少女肖像**<br>(`sunlit_window_portrait`) | `8.62 → 8.98 →` **`9.26`**<br>经过 3 轮达标 ✅ | `8.75 → 9.20 →` **`9.54`**<br>经过 3 轮达标 ✅ | `8.68 → 8.77 →` **`9.84`**<br>经过 3 轮达标 🏆（盲评 `9.21`） | `8.70 → 9.18 →` **`9.71`**（经过 3 轮达标 🎯）<br>方向：*拉远为古典木质温室花房中景全身构图* |
| **案例 04 (W01) · 奇幻垂直峡谷巷道**<br>(`web_01_vertical_alley`) | `8.60 → 8.96 →` **`9.23`**<br>经过 3 轮达标 ✅ | `8.70 → 9.18 →` **`9.51`**<br>经过 3 轮达标 ✅ | `8.75 → 8.84 →` **`9.81`**<br>经过 3 轮达标 🏆（盲评 `9.35`） | `8.65 → 9.15 →` **`9.69`**（经过 3 轮达标 🎯）<br>方向：*改为谷底溪流木船第一人称极限仰视* |

---

### 🔍 独立 VLM 裁判乱序盲评验证（`BLIND_ART_01..12`）与 Cursor 防自评虚高机制

为什么之前会出现“第 2 轮自评 9.65 分、但肉眼看还不如单次直出”的现象？因为**让刚写完 Prompt 的同一个模型自己评自己的图，会产生严重的「提示词确认偏误」**。为此我们在 `skills_kit.py` 中内置了 `build_blind_judge_prompt()` 与 `audit_score_inflation()`，并将 12 张候选图匿名乱序交给独立 VLM 盲评：
- **精准戳破第 2 轮同会话自评虚高（`+0.51 ~ +0.99` 分）**：案例 02 第 2 轮自评 `9.65` → 独立盲评仅 **`8.66`**；案例 03 第 2 轮自评 `9.72` → 独立盲评仅 **`8.77`**，全部未满高强度阈值，强制触发第 3 轮深度重构！
- **独立盲评实测证实第 3 轮全面跃升**：
  - **案例 04（奇幻峡谷）**：第 2 轮盲评 `8.84` → **经过 3 轮达标定稿盲评 `9.35`（跃升 `+0.51` 分，全场最高）**
  - **案例 03（窗边少女）**：第 2 轮盲评 `8.77` → **经过 3 轮达标定稿盲评 `9.21`（跃升 `+0.44` 分）**
  - **W02（北欧峡湾水彩）**：第 2 轮盲评 `8.84` → **经过 3 轮达标定稿盲评 `9.20`（跃升 `+0.36` 分）**
  - **W03（索罗亚厚涂肖像）**：第 2 轮盲评 `8.81` → **经过 3 轮达标定稿盲评 `9.06`（跃升 `+0.25` 分）**
  - **案例 02（油画棒少女）**：第 2 轮盲评 `8.66` → **经过 3 轮达标定稿盲评 `8.88`（跃升 `+0.22` 分）**


# 🎨 pmem-art

> **一句话流程：输入任意风格参考原图（Style Reference）→ 基于 `~/.pmem-art/shared/` 全局底层美术记忆拆解原图基因 → 按 `low / medium / high / recompose` 强度自动执行 `R1 → R2 → R3 ... → R8` 五维严苛审图与提示词演进闭环，收敛出 Showcase 级终极定稿并沉淀项目专属记忆。**

[![Showcase HTML](https://img.shields.io/badge/Interactive_Gallery-pmem__art__showcase.html-f59e0b?style=for-the-badge)](comparison/pmem_art_showcase.html)
[![Rules & 5D Rubric](https://img.shields.io/badge/Docs-规则手册与五维权重细则-38bdf8?style=for-the-badge)](docs/RULES_AND_RUBRIC.md)
[![Architecture](https://img.shields.io/badge/Docs-双层记忆架构说明-10b981?style=for-the-badge)](ARCHITECTURE.md)

---

## 🖼️ 一、风格参考原图三轮演进（`Style Reference → R1 → R2 → R3` · 空项目冷启动仅全局基础记忆）

### 案例 01 · 东方仙侠不夜城高空原画 (`pmem_01_celestial_night_city`)
| 参考原图 (`Style Reference`) | `pmem-art` R1 (`9.12`) | `pmem-art` R2 (`9.36`) | `pmem-art` **R3 终极定稿 (`9.82`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/style_refs/style_ref_01_night_city.png" width="210"/> | <img src="comparison/pmem_01_celestial_night_city_r1.jpg" width="210"/> | <img src="comparison/pmem_01_celestial_night_city_r2.jpg" width="210"/> | <img src="comparison/pmem_01_celestial_night_city_r3.jpg" width="210"/> |

### 案例 02 · 300g 冷压粗纹纸油画棒少女 (`pmem_02_pastel_sketch_girl` · 粗纹纸飞白空气感 + 黑红明度层次跃升)
| 参考原图 (`Style Reference`) | `pmem-art` R1 (`8.65`) | `pmem-art` R2 (严苛校准 `8.80`) | `pmem-art` **R3 终极定稿 (`9.78`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/style_refs/style_ref_02_pastel_sketch.png" width="210"/> | <img src="comparison/pmem_02_pastel_sketch_girl_r1.jpg" width="210"/> | <img src="comparison/pmem_02_pastel_sketch_girl_r2.jpg" width="210"/> | <img src="comparison/pmem_02_pastel_sketch_girl_r3.jpg" width="210"/> |

### 案例 03 · 窗边木漏日逆光少女肖像 (`pmem_03_sunlit_window_portrait` · 打破正面平视重构 3/4 倚窗回眸)
| 参考原图 (`Style Reference`) | `pmem-art` R1 (`8.72`) | `pmem-art` R2 (严苛校准 `8.88`) | `pmem-art` **R3 终极定稿 (`9.84`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/style_refs/style_ref_03_sunlit_portrait.png" width="210"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r1.jpg" width="210"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r2.jpg" width="210"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r3.jpg" width="210"/> |

### 案例 W01 · 奇幻峡谷垂直巷道概念设计 (`web_01_vertical_alley`)
| 参考原图 (`Style Reference`) | `pmem-art` R1 (`9.08`) | `pmem-art` R2 (`9.38`) | `pmem-art` **R3 终极定稿 (`9.81`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/web_refs/web_ref_01_concept_ishtar.png" width="210"/> | <img src="comparison/web_01_vertical_alley_r1.jpg" width="210"/> | <img src="comparison/web_01_vertical_alley_r2.jpg" width="210"/> | <img src="comparison/web_01_vertical_alley_r3.jpg" width="210"/> |

### 案例 W02 · 北欧峡湾木屋港口绘本水彩插画 (`web_02_nordic_harbor`)
| 参考原图 (`Style Reference`) | `pmem-art` R1 (`9.05`) | `pmem-art` R2 (`9.35`) | `pmem-art` **R3 终极定稿 (`9.80`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/web_refs/web_ref_02_illustration_bergen.jpg" width="210"/> | <img src="comparison/web_02_nordic_harbor_r1.jpg" width="210"/> | <img src="comparison/web_02_nordic_harbor_r2.jpg" width="210"/> | <img src="comparison/web_02_nordic_harbor_r3.jpg" width="210"/> |

### 案例 W03 · 印象派光影厚涂油画肖像 (`web_03_impressionist_portrait`)
| 参考原图 (`Style Reference`) | `pmem-art` R1 (`9.10`) | `pmem-art` R2 (`9.40`) | `pmem-art` **R3 终极定稿 (`9.83`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/web_refs/web_ref_03_portrait_sorolla.jpg" width="210"/> | <img src="comparison/web_03_impressionist_portrait_r1.jpg" width="210"/> | <img src="comparison/web_03_impressionist_portrait_r2.jpg" width="210"/> | <img src="comparison/web_03_impressionist_portrait_r3.jpg" width="210"/> |

---

## 🎚️ 二、能力边界矩阵：低 / 中 / 高三种收敛强度 + 用户指定「改构图 (`--scale recompose`)」

| 风格组 | 参考原图 (`Style Reference`) | 低强度 (`--scale low` · 只修缺陷) | 中强度 (`--scale medium` · 补足加小优化) | 高强度 (`--scale high` · 大胆重构光影) | 定向改构图 (`--scale recompose` · 用户指定新构图) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A. 仙侠不夜城** | <img src="comparison/style_refs/style_ref_01_night_city.png" width="150"/> | <img src="comparison/scale_01_night_city_low.jpg" width="150"/><br/><sub>锁死机位，仅修屋瓦与长剑</sub> | <img src="comparison/pmem_01_celestial_night_city_r2.jpg" width="150"/><br/><sub>补充孔明灯与弧形天际线</sub> | <img src="comparison/pmem_01_celestial_night_city_r3.jpg" width="150"/><br/><sub>朱红长绸+寒霜剑气+崖壁飞瀑</sub> | <img src="comparison/scale_01_night_city_recompose.jpg" width="150"/><br/><sub>**改构图**：高空俯瞰 → 运河石拱桥仰视全景</sub> |
| **B. 粗纹纸油画棒** | <img src="comparison/style_refs/style_ref_02_pastel_sketch.png" width="150"/> | <img src="comparison/scale_02_sketch_low.jpg" width="150"/><br/><sub>锁死原坐姿，仅修五指与纸纹</sub> | <img src="comparison/pmem_02_pastel_sketch_girl_r2.jpg" width="150"/><br/><sub>补充背景右上暖光与左下冷影</sub> | <img src="comparison/pmem_02_pastel_sketch_girl_r3.jpg" width="150"/><br/><sub>300g飞白+黑耳机红帽衫对比+丁达尔光束</sub> | <img src="comparison/scale_02_sketch_recompose.jpg" width="150"/><br/><sub>**改构图**：地面坐姿近景 → 天台凭栏远眺夕阳海港全景</sub> |
| **C. 窗边逆光肖像** | <img src="comparison/style_refs/style_ref_03_sunlit_portrait.png" width="150"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r1.jpg" width="150"/><br/><sub>锁死正面平视，仅修发丝与胶片颗粒</sub> | <img src="comparison/pmem_03_sunlit_window_portrait_r2.jpg" width="150"/><br/><sub>补充逆光金边与空气微尘</sub> | <img src="comparison/pmem_03_sunlit_window_portrait_r3.jpg" width="150"/><br/><sub>3/4倚窗回眸+绣球花蕾丝木漏日斑驳光影</sub> | <img src="comparison/scale_03_portrait_recompose.jpg" width="150"/><br/><sub>**改构图**：胸像正面特写 → 阳光植物画室藤椅全景</sub> |
| **D. 奇幻峡谷城邦** | <img src="comparison/web_refs/web_ref_01_concept_ishtar.png" width="150"/> | <img src="comparison/web_01_vertical_alley_r1.jpg" width="150"/><br/><sub>锁死天井俯视，仅修石砖与木桥透视</sub> | <img src="comparison/web_01_vertical_alley_r2.jpg" width="150"/><br/><sub>补充前景绿龙与谷底蓝光雾气</sub> | <img src="comparison/web_01_vertical_alley_r3.jpg" width="150"/><br/><sub>丁达尔金光劈入峡谷+绯红战旗+石桥行人</sub> | <img src="comparison/scale_04_canyon_recompose.jpg" width="150"/><br/><sub>**改构图**：狭窄天井俯视 → 悬崖露台远眺千丈跨谷大桥全景</sub> |

---

## 🔍 三、独立 VLM 裁判乱序盲评验证 & Cursor「生成/审图解耦」防虚高机制

在 Cursor 等 AI IDE 中，如果让**刚写完 Prompt 的同一个生成会话直接给自己打分**，极易产生**提示词确认偏误（Prompt Confirmation Bias）**，在 R2 给出 `9.6+` 虚高分提前终止收敛。为此，`pmem-art` 采用 **「代码级五维反虚高硬拦截 + 独立零上下文 VLM 裁判盲评」** 双重解耦机制：

| 样本组 | R2 旧版同会话自评 | **R2 独立 VLM 乱序盲评** | **R3 独立 VLM 乱序盲评** | 独立裁判盲评跃升 (`R2 → R3`) 与核心诊断 |
| :--- | :---: | :---: | :---: | :--- |
| **案例 02 · 300g 粗纹纸油画棒少女** | ~~9.65~~ | `8.66` | **`8.88` 🏆** | **拦截 `+0.99` 虚高 → 盲评跃升 `+0.22`**：R3 补齐 300g 粗纹纸飞白留白、黑耳机黑背包明度压重音与右上丁达尔光束 |
| **案例 03 · 窗边木漏日逆光少女** | ~~9.72~~ | `8.77` | **`9.21` 🏆** | **拦截 `+0.95` 虚高 → 盲评跃升 `+0.44`**：R3 打破正面平视大头照，重构为 3/4 倚窗回眸 + 绣球花蕾丝木漏日（光影获 `9.5` 分） |
| **案例 W01 · 奇幻峡谷垂直巷道** | ~~9.38~~ | `8.84` | **`9.35` 🏆** | **拦截 `+0.54` 虚高 → 盲评跃升 `+0.51`（全场最高）**：右上裂谷金色丁达尔神光 (`9.5`) 与多层栈桥、前景巨龙锚点 |
| **案例 W02 · 北欧峡湾木屋港口** | ~~9.35~~ | `8.84` | **`9.20` 🏆** | **拦截 `+0.51` 虚高 → 盲评跃升 `+0.36`**：湿润鹅卵石倒影 + 夕阳逆光与手提黄铜灯笼双光源 (`9.3`) |
| **案例 W03 · 印象派厚涂肖像** | ~~9.40~~ | `8.81` | **`9.06` 🏆** | **拦截 `+0.59` 虚高 → 盲评跃升 `+0.25`**：打通索罗亚式地中海阳光柱廊与碧海远景，光影升至 `9.3`、厚涂质感升至 `9.2` |

- **代码级防虚高审计 (`skills_kit.py`)**：`parse_5d_dims()` 强制按五维权重核算总分；`audit_score_inflation()` 一旦检测到 `--defects` 含 `缺乏飞白 / 数字化 / 照搬 / 仅微调 / 呆板 / 平光 / 颗粒太均匀` 等短板词，强制将得分硬顶封死在 `<= 8.90` 并推入下一轮（R3..R8）。
- **独立裁判可插拔架构**：在 Cursor 内使用时，支持由**零上下文独立审图子智能体**或**接入外部异构 VLM 模型 API** 只看图打分并自动回填 `.memory-art/converge/*.json`，彻底杜绝同会话“自生自评自嗨”。

---

## 📚 详细文档导航

- 🎨 **[完整交互式画廊 (`comparison/pmem_art_showcase.html`)](comparison/pmem_art_showcase.html)**：内嵌全套 `Style Reference → R1 → R2 → R3` 演进大图、每轮完整英文 Prompt、五维审图记录与 `Low / Medium / High / Recompose` 四档实测矩阵。
- 📐 **[规则手册与五维审图权重细则 (`docs/RULES_AND_RUBRIC.md`)](docs/RULES_AND_RUBRIC.md)**：双层记忆架构、4 层模块硬顶、`--scale low|medium|high|recompose` 内部权重表与五维反虚高评分准则。
- 🏗️ **[系统架构文档 (`ARCHITECTURE.md`)](ARCHITECTURE.md)**：Layer 1 项目专项记忆库 (`.memory-art/projects/<slug>/`) 与 Layer 2 全局基础工艺库 (`~/.pmem-art/shared/`) 详细设计。
