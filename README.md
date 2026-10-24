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
