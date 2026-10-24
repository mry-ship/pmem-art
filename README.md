# 🎨 pmem-art

> **一句话流程：输入任意参考原图 → 基于 `~/.pmem-art/shared/` 全局底层美术记忆拆解原图基因 → 按 `low / medium / high / recompose` 强度执行 `R1 → R2 → R3` 五维严苛审图与提示词演进闭环，自动收敛出 Showcase 级终极定稿并沉淀项目专属记忆。**

[![Showcase HTML](https://img.shields.io/badge/Interactive_Gallery-pmem__vs__market__showcase.html-f59e0b?style=for-the-badge)](comparison/pmem_vs_market_showcase.html)
[![Rules & 5D Rubric](https://img.shields.io/badge/Docs-规则手册与五维权重细则-38bdf8?style=for-the-badge)](docs/RULES_AND_RUBRIC.md)
[![Architecture](https://img.shields.io/badge/Docs-双层记忆架构说明-10b981?style=for-the-badge)](ARCHITECTURE.md)

---

## 🖼️ 一、基准原图三轮演进（`R1 → R2 → R3` · 空项目冷启动仅全局基础记忆）

### 案例 01 · 东方仙侠不夜城高空原画 (`pmem_01_celestial_night_city`)
| 参考原图 (`Ref`) | Market Baseline (`gpt-image-2` · `8.85`) | `pmem-art` R1 (`9.12`) | `pmem-art` R2 (`9.36`) | `pmem-art` **R3 终极定稿 (`9.82`)** |
| :---: | :---: | :---: | :---: | :---: |
| <img src="comparison/aether_refs/aether-1-night-city-ref.png" width="180"/> | <img src="comparison/aether_refs/aether-1-night-city-out.png" width="180"/> | <img src="comparison/pmem_01_celestial_night_city_r1.jpg" width="180"/> | <img src="comparison/pmem_01_celestial_night_city_r2.jpg" width="180"/> | <img src="comparison/pmem_01_celestial_night_city_r3.jpg" width="180"/> |

### 案例 02 · 300g 冷压粗纹纸油画棒少女 (`pmem_02_pastel_sketch_girl` · 严苛重审校准 + R3 质感跃升)
| 参考原图 (`Ref`) | Market Baseline (`gpt-image-2` · `8.86`) | `pmem-art` R1 (`8.65`) | `pmem-art` R2 (严苛校准 `8.80`) | `pmem-art` **R3 终极定稿 (`9.78`)** |
| :---: | :---: | :---: | :---: | :---: |
| <img src="comparison/aether_refs/aether-2-sketch-ref.png" width="180"/> | <img src="comparison/aether_refs/aether-2-sketch-out.png" width="180"/> | <img src="comparison/pmem_02_pastel_sketch_girl_r1.jpg" width="180"/> | <img src="comparison/pmem_02_pastel_sketch_girl_r2.jpg" width="180"/> | <img src="comparison/pmem_02_pastel_sketch_girl_r3.jpg" width="180"/> |

### 案例 03 · 窗边木漏日逆光少女肖像 (`pmem_03_sunlit_window_portrait` · R3 打破平视证件照重构 3/4 倚窗回眸)
| 参考原图 (`Ref`) | Market Baseline (`gpt-image-2` · `8.92`) | `pmem-art` R1 (`8.72`) | `pmem-art` R2 (严苛校准 `8.88`) | `pmem-art` **R3 终极定稿 (`9.84`)** |
| :---: | :---: | :---: | :---: | :---: |
| <img src="comparison/aether_refs/aether-3-portrait-ref.png" width="180"/> | <img src="comparison/aether_refs/aether-3-portrait-out.png" width="180"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r1.jpg" width="180"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r2.jpg" width="180"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r3.jpg" width="180"/> |

---

## 🌍 二、独立跨风格新图三轮演进（`W01–W03` · 零外部提示词冷启动）

### 独立案例 W01 · 奇幻峡谷垂直巷道概念设计 (`web_01_vertical_alley`)
| 独立参考原图 (`Ref`) | `pmem-art` R1 (`9.08`) | `pmem-art` R2 (`9.38`) | `pmem-art` **R3 终极定稿 (`9.81`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/web_refs/web_ref_01_concept_ishtar.png" width="210"/> | <img src="comparison/web_01_vertical_alley_r1.jpg" width="210"/> | <img src="comparison/web_01_vertical_alley_r2.jpg" width="210"/> | <img src="comparison/web_01_vertical_alley_r3.jpg" width="210"/> |

### 独立案例 W02 · 北欧峡湾木屋港口绘本水彩插画 (`web_02_nordic_harbor`)
| 独立参考原图 (`Ref`) | `pmem-art` R1 (`9.05`) | `pmem-art` R2 (`9.35`) | `pmem-art` **R3 终极定稿 (`9.80`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/web_refs/web_ref_02_illustration_bergen.jpg" width="210"/> | <img src="comparison/web_02_nordic_harbor_r1.jpg" width="210"/> | <img src="comparison/web_02_nordic_harbor_r2.jpg" width="210"/> | <img src="comparison/web_02_nordic_harbor_r3.jpg" width="210"/> |

### 独立案例 W03 · 印象派光影厚涂油画肖像 (`web_03_impressionist_portrait`)
| 独立参考原图 (`Ref`) | `pmem-art` R1 (`9.10`) | `pmem-art` R2 (`9.40`) | `pmem-art` **R3 终极定稿 (`9.83`)** |
| :---: | :---: | :---: | :---: |
| <img src="comparison/web_refs/web_ref_03_portrait_sorolla.jpg" width="210"/> | <img src="comparison/web_03_impressionist_portrait_r1.jpg" width="210"/> | <img src="comparison/web_03_impressionist_portrait_r2.jpg" width="210"/> | <img src="comparison/web_03_impressionist_portrait_r3.jpg" width="210"/> |

---

## 🎚️ 三、能力边界矩阵：低 / 中 / 高三种收敛强度 + 用户指定「改构图 (`--scale recompose`)」

| 风格组 | 参考原图 (`Ref`) | 低强度 (`--scale low` · 只修缺陷) | 中强度 (`--scale medium` · 补足加小优化) | 高强度 (`--scale high` · 大胆重构光影) | 定向改构图 (`--scale recompose` · 用户指定新构图) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A. 仙侠不夜城** | <img src="comparison/aether_refs/aether-1-night-city-ref.png" width="150"/> | <img src="comparison/scale_01_night_city_low.jpg" width="150"/><br/><sub>锁死机位，仅修屋瓦与长剑</sub> | <img src="comparison/pmem_01_celestial_night_city_r2.jpg" width="150"/><br/><sub>补充孔明灯与弧形天际线</sub> | <img src="comparison/pmem_01_celestial_night_city_r3.jpg" width="150"/><br/><sub>朱红长绸+寒霜剑气+崖壁飞瀑</sub> | <img src="comparison/scale_01_night_city_recompose.jpg" width="150"/><br/><sub>**改构图**：高空俯瞰 → 运河石拱桥仰视全景</sub> |
| **B. 粗纹纸油画棒** | <img src="comparison/aether_refs/aether-2-sketch-ref.png" width="150"/> | <img src="comparison/scale_02_sketch_low.jpg" width="150"/><br/><sub>锁死原坐姿，仅修五指与纸纹</sub> | <img src="comparison/pmem_02_pastel_sketch_girl_r2.jpg" width="150"/><br/><sub>补充背景右上暖光与左下冷影</sub> | <img src="comparison/pmem_02_pastel_sketch_girl_r3.jpg" width="150"/><br/><sub>300g飞白+黑耳机红帽衫对比+丁达尔光束</sub> | <img src="comparison/scale_02_sketch_recompose.jpg" width="150"/><br/><sub>**改构图**：地面坐姿近景 → 天台凭栏远眺夕阳海港全景</sub> |
| **C. 窗边逆光肖像** | <img src="comparison/aether_refs/aether-3-portrait-ref.png" width="150"/> | <img src="comparison/pmem_03_sunlit_window_portrait_r1.jpg" width="150"/><br/><sub>锁死正面平视，仅修发丝与胶片颗粒</sub> | <img src="comparison/pmem_03_sunlit_window_portrait_r2.jpg" width="150"/><br/><sub>补充逆光金边与空气微尘</sub> | <img src="comparison/pmem_03_sunlit_window_portrait_r3.jpg" width="150"/><br/><sub>3/4倚窗回眸+绣球花蕾丝木漏日斑驳光影</sub> | <img src="comparison/scale_03_portrait_recompose.jpg" width="150"/><br/><sub>**改构图**：胸像正面特写 → 阳光植物画室藤椅全景</sub> |
| **D. 奇幻峡谷城邦** | <img src="comparison/web_refs/web_ref_01_concept_ishtar.png" width="150"/> | <img src="comparison/web_01_vertical_alley_r1.jpg" width="150"/><br/><sub>锁死天井俯视，仅修石砖与木桥透视</sub> | <img src="comparison/web_01_vertical_alley_r2.jpg" width="150"/><br/><sub>补充前景绿龙与谷底蓝光雾气</sub> | <img src="comparison/web_01_vertical_alley_r3.jpg" width="150"/><br/><sub>丁达尔金光劈入峡谷+绯红战旗+石桥行人</sub> | <img src="comparison/scale_04_canyon_recompose.jpg" width="150"/><br/><sub>**改构图**：狭窄天井俯视 → 悬崖露台远眺千丈跨谷大桥全景</sub> |

---

## 📚 详细文档导航

- 🎨 **[完整交互式对比画廊 (`comparison/pmem_vs_market_showcase.html`)](comparison/pmem_vs_market_showcase.html)**：内嵌全部 26 张对比大图、每轮完整英文 Prompt、五维严苛审图评分表、Case 02 虚高复盘、`Low / Medium / High / Recompose` 四档实测矩阵与 Step 1–6 全链路时间线。
- 📐 **[规则手册与五维审图权重细则 (`docs/RULES_AND_RUBRIC.md`)](docs/RULES_AND_RUBRIC.md)**：双层记忆架构、4 层模块硬顶、`--scale low|medium|high|recompose` 内部权重表与五维反虚高评分准则。
- 🏗️ **[系统架构文档 (`ARCHITECTURE.md`)](ARCHITECTURE.md)**：Layer 1 项目专项记忆库 (`.memory-art/projects/<slug>/`) 与 Layer 2 全局基础工艺库 (`~/.pmem-art/shared/`) 详细设计。
