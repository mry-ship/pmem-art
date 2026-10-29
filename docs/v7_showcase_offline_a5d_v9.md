# V7 Showcase 离线 Absolute-5D（v9.1_audit_patch）

- 合同+审计补丁 · STOP=8.5 · prior=7.0
- 成功 36/36 · mean=8.34 · range 7.32–8.59
- ≥8.5=14 · ≥7=36 · <5=0
- vs VLM: meanΔ=0.37 · MAE=0.5 · |Δ|≤1: 32/36 · |Δ|≤1.5: 36/36
- 原图基线: {'night_city': 8.1, 'pastel_sketch': 7.74, 'sunlit_portrait': 8.1, 'ishtar_canyon': 8.03}
- 分案均分: {'ishtar_canyon': 8.41, 'night_city': 8.1, 'pastel_sketch': 8.38, 'sunlit_portrait': 8.49}

| case | role | file | offline | Δref | VLM | Δ(off−VLM) | defects |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| night_city | baseline_ref | `style_ref_01_night_city.png` | 8.1 | 0.0 | 8.17 | -0.07 |  |
| pastel_sketch | baseline_ref | `style_ref_02_pastel_sketch.png` | 7.74 | 0.0 | 6.9 | 0.84 |  |
| sunlit_portrait | baseline_ref | `style_ref_03_sunlit_portrait.png` | 8.1 | 0.0 | 7.71 | 0.39 |  |
| night_city | low | `v7_bot_01_night_city_low.jpg` | 7.32 | -0.78 | 8.12 | -0.8 |  |
| night_city | low_best | `v7_bot_02_night_city_low_best.jpg` | 8.13 | 0.03 | 8.29 | -0.16 |  |
| night_city | medium | `v7_bot_03_night_city_medium.jpg` | 8.13 | 0.03 | 7.93 | 0.2 |  |
| night_city | medium_best | `v7_bot_04_night_city_medium_best.jpg` | 8.59 | 0.49 | 8.15 | 0.44 |  |
| night_city | high | `v7_bot_05_night_city_high.jpg` | 8.13 | 0.03 | 8.43 | -0.3 |  |
| night_city | high_best | `v7_bot_06_night_city_high_best.jpg` | 8.59 | 0.49 | 8.34 | 0.25 |  |
| night_city | recompose | `v7_bot_07_night_city_recompose.jpg` | 8.24 | 0.14 | 7.91 | 0.33 |  |
| night_city | recompose_bold | `v7_bot_08_night_city_recompose_bold.jpg` | 7.65 | -0.45 | 8.38 | -0.73 | 死黑/过曝失控 |
| pastel_sketch | low | `v7_bot_09_pastel_sketch_low.jpg` | 8.3 | 0.56 | 6.92 | 1.38 |  |
| pastel_sketch | low_best | `v7_bot_10_pastel_sketch_low_best.jpg` | 8.3 | 0.56 | 7.08 | 1.22 |  |
| pastel_sketch | medium | `v7_bot_11_pastel_sketch_medium.jpg` | 8.59 | 0.85 | 7.45 | 1.14 |  |
| pastel_sketch | medium_best | `v7_bot_12_pastel_sketch_medium_best.jpg` | 8.59 | 0.85 | 7.32 | 1.27 |  |
| pastel_sketch | high | `v7_bot_13_pastel_sketch_high.jpg` | 8.37 | 0.63 | 7.63 | 0.74 |  |
| pastel_sketch | high_best | `v7_bot_14_pastel_sketch_high_best.jpg` | 8.37 | 0.63 | 7.76 | 0.61 |  |
| pastel_sketch | recompose | `v7_bot_15_pastel_sketch_recompose.jpg` | 8.59 | 0.85 | 7.98 | 0.61 |  |
| pastel_sketch | recompose_bold | `v7_bot_16_pastel_sketch_recompose_bold.jpg` | 8.59 | 0.85 | 7.83 | 0.76 |  |
| sunlit_portrait | low | `v7_bot_17_sunlit_portrait_low.jpg` | 8.59 | 0.49 | 8.28 | 0.31 |  |
| sunlit_portrait | low_best | `v7_bot_18_sunlit_portrait_low_best.jpg` | 8.59 | 0.49 | 8.27 | 0.32 |  |
| sunlit_portrait | medium | `v7_bot_19_sunlit_portrait_medium.jpg` | 8.44 | 0.34 | 7.79 | 0.65 |  |
| sunlit_portrait | medium_best | `v7_bot_20_sunlit_portrait_medium_best.jpg` | 8.44 | 0.34 | 8.12 | 0.32 |  |
| sunlit_portrait | high | `v7_bot_21_sunlit_portrait_high.jpg` | 8.59 | 0.49 | 8.53 | 0.06 |  |
| sunlit_portrait | high_best | `v7_bot_22_sunlit_portrait_high_best.jpg` | 8.59 | 0.49 | 8.33 | 0.26 |  |
| sunlit_portrait | recompose | `v7_bot_23_sunlit_portrait_recompose.jpg` | 8.44 | 0.34 | 8.37 | 0.07 |  |
| sunlit_portrait | recompose_bold | `v7_bot_24_sunlit_portrait_recompose_bold.jpg` | 8.59 | 0.49 | 8.06 | 0.53 |  |
| ishtar_canyon | low | `v7_bot_25_ishtar_canyon_low.jpg` | 8.37 | 0.34 | 8.03 | 0.34 |  |
| ishtar_canyon | low_best | `v7_bot_26_ishtar_canyon_low_best.jpg` | 8.37 | 0.34 | 7.93 | 0.44 |  |
| ishtar_canyon | medium | `v7_bot_27_ishtar_canyon_medium.jpg` | 8.37 | 0.34 | 7.94 | 0.43 |  |
| ishtar_canyon | medium_best | `v7_bot_28_ishtar_canyon_medium_best.jpg` | 8.59 | 0.56 | 7.77 | 0.82 |  |
| ishtar_canyon | high | `v7_bot_29_ishtar_canyon_high.jpg` | 8.37 | 0.34 | 8.26 | 0.11 |  |
| ishtar_canyon | high_best | `v7_bot_30_ishtar_canyon_high_best.jpg` | 8.59 | 0.56 | 8.26 | 0.33 |  |
| ishtar_canyon | recompose | `v7_bot_31_ishtar_canyon_recompose.jpg` | 8.59 | 0.56 | 8.21 | 0.38 |  |
| ishtar_canyon | recompose_bold | `v7_bot_32_ishtar_canyon_recompose_bold.jpg` | 8.37 | 0.34 | 8.55 | -0.18 |  |
| ishtar_canyon | baseline_ref | `web_ref_01_concept_ishtar.png` | 8.03 | 0.0 | 7.87 | 0.16 |  |
