# VLM Absolute-5D V7 Report

- **Model used**: `gpt-6-sol` (env `cursor-gpt` not listed / 404; `gpt-6.1-sol` timed out with 0 bytes — switched to working vision model)
- **Endpoint**: `https://YOUR_VLM_GATEWAY/v1/chat/completions`
- **Scored**: 52 unique images (4 baseline refs + 32 bot finals + 16 `_rN` intermediates); sha256-deduped; failures after retry: **0**
- **Dims**: `composition, lighting_color, perspective_anatomy, texture_detail, spec_style` (match `scripts/absolute_5d_scorer.py`)
- **Aggregation**: `total` = scale-weighted; `total_mean` = simple mean of 5 dims
- **Time zone note**: scores collected Asia/Shanghai local on box

## Distribution (weighted `total`)

| Group | n | min | median | mean | max | <7 | 7–8 | 8–9 | ≥9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 4 | 6.95 | 7.39 | 7.36 | 7.69 | 1 | 3 | 0 | 0 |
| bot_final | 32 | 7.16 | 7.83 | 7.87 | 8.78 | 0 | 19 | 13 | 0 |
| round_rN | 16 | 7.55 | 7.94 | 7.95 | 8.28 | 0 | 11 | 5 | 0 |
| all | 52 | 6.95 | 7.84 | 7.85 | 8.78 | 1 | 33 | 18 | 0 |

### Dim means (baseline vs bot finals)

| Dim | baseline | bot_final |
| --- | ---: | ---: |
| composition | 7.7 | 8.13 |
| lighting_color | 7.47 | 8.26 |
| perspective_anatomy | 7.03 | 7.38 |
| texture_detail | 7.05 | 7.41 |
| spec_style | 7.62 | 8.05 |

## Comparison vs prior heuristic ~9.0 cluster

Prior heuristic Absolute-5D (v7_image_scorer / early absolute) clustered near ~9.0, partly because baseline used (ref,ref)+struct and soft plates were not gated. This VLM pass (model=gpt-6-sol) spreads roughly 6.95–8.78 (mean 7.85, median 7.84), showing why the old ~9 cluster was not an honest absolute ruler.

## Notable lows

- `style_ref_01_night_city.png` (baseline) **6.95** — {'composition': 8.0, 'lighting_color': 7.2, 'perspective_anatomy': 6.7, 'texture_detail': 5.9, 'spec_style': 7.1}
- `v7_bot_02_night_city_low_best.jpg` (bot) **7.16** — {'composition': 7.8, 'lighting_color': 7.5, 'perspective_anatomy': 7.0, 'texture_detail': 6.5, 'spec_style': 7.4}
- `v7_bot_01_night_city_low.jpg` (bot) **7.23** — {'composition': 8.1, 'lighting_color': 7.7, 'perspective_anatomy': 7.1, 'texture_detail': 6.3, 'spec_style': 7.5}
- `style_ref_02_pastel_sketch.png` (baseline) **7.3** — {'composition': 7.6, 'lighting_color': 7.1, 'perspective_anatomy': 6.8, 'texture_detail': 7.5, 'spec_style': 7.8}
- `v7_bot_11_pastel_sketch_medium.jpg` (bot) **7.3** — {'composition': 7.6, 'lighting_color': 7.8, 'perspective_anatomy': 6.8, 'texture_detail': 6.7, 'spec_style': 7.5}
- `v7_bot_09_pastel_sketch_low.jpg` (bot) **7.34** — {'composition': 7.8, 'lighting_color': 7.5, 'perspective_anatomy': 6.7, 'texture_detail': 7.3, 'spec_style': 7.8}
- `web_ref_01_concept_ishtar.png` (baseline) **7.49** — {'composition': 7.6, 'lighting_color': 7.4, 'perspective_anatomy': 7.1, 'texture_detail': 7.7, 'spec_style': 7.8}
- `v7_bot_12_pastel_sketch_medium_best.jpg` (bot) **7.49** — {'composition': 7.8, 'lighting_color': 7.4, 'perspective_anatomy': 7.0, 'texture_detail': 7.5, 'spec_style': 8.0}

## Notable highs

- `v7_bot_32_ishtar_canyon_recompose_bold.jpg` (bot) **8.78** — {'composition': 9.0, 'lighting_color': 9.1, 'perspective_anatomy': 8.4, 'texture_detail': 8.3, 'spec_style': 8.9}
- `v7_bot_30_ishtar_canyon_high_best.jpg` (bot) **8.72** — {'composition': 9.1, 'lighting_color': 9.3, 'perspective_anatomy': 7.8, 'texture_detail': 8.2, 'spec_style': 8.8}
- `v7_bot_21_sunlit_portrait_high.jpg` (bot) **8.29** — {'composition': 8.1, 'lighting_color': 8.8, 'perspective_anatomy': 7.8, 'texture_detail': 7.9, 'spec_style': 8.4}
- `v7_bot_30_ishtar_canyon_high_best_r1.jpg` (round_r1) **8.28** — {'composition': 8.5, 'lighting_color': 8.8, 'perspective_anatomy': 7.6, 'texture_detail': 7.8, 'spec_style': 8.3}
- `v7_bot_15_pastel_sketch_recompose_r1.jpg` (round_r1) **8.21** — {'composition': 8.2, 'lighting_color': 8.7, 'perspective_anatomy': 7.8, 'texture_detail': 7.9, 'spec_style': 8.4}
- `v7_bot_06_night_city_high_best.jpg` (bot) **8.2** — {'composition': 8.5, 'lighting_color': 8.7, 'perspective_anatomy': 7.7, 'texture_detail': 7.5, 'spec_style': 8.3}
- `v7_bot_05_night_city_high.jpg` (bot) **8.19** — {'composition': 8.7, 'lighting_color': 8.8, 'perspective_anatomy': 7.5, 'texture_detail': 7.3, 'spec_style': 8.3}
- `v7_bot_08_night_city_recompose_bold.jpg` (bot) **8.17** — {'composition': 8.7, 'lighting_color': 8.8, 'perspective_anatomy': 7.2, 'texture_detail': 7.4, 'spec_style': 8.3}

## Sample rows (10)

| file | role | scale | total | mean | composition | lighting_color | perspective_anatomy | texture_detail | spec_style |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `style_ref_01_night_city.png` | baseline | medium | 6.95 | 6.98 | 8.0 | 7.2 | 6.7 | 5.9 | 7.1 |
| `style_ref_03_sunlit_portrait.png` | baseline | medium | 7.69 | 7.64 | 7.6 | 8.2 | 7.5 | 7.1 | 7.8 |
| `style_ref_02_pastel_sketch.png` | baseline | medium | 7.3 | 7.36 | 7.6 | 7.1 | 6.8 | 7.5 | 7.8 |
| `web_ref_01_concept_ishtar.png` | baseline | medium | 7.49 | 7.52 | 7.6 | 7.4 | 7.1 | 7.7 | 7.8 |
| `v7_bot_02_night_city_low_best.jpg` | bot | low | 7.16 | 7.24 | 7.8 | 7.5 | 7.0 | 6.5 | 7.4 |
| `v7_bot_20_sunlit_portrait_medium_best.jpg` | bot | medium | 7.62 | 7.58 | 7.7 | 8.2 | 7.2 | 7.0 | 7.8 |
| `v7_bot_25_ishtar_canyon_low.jpg` | bot | low | 7.83 | 7.88 | 8.0 | 8.3 | 7.2 | 7.8 | 8.1 |
| `v7_bot_13_pastel_sketch_high.jpg` | bot | high | 8.13 | 8.06 | 8.0 | 8.5 | 7.5 | 8.1 | 8.2 |
| `v7_bot_30_ishtar_canyon_high_best.jpg` | bot | high | 8.72 | 8.64 | 9.1 | 9.3 | 7.8 | 8.2 | 8.8 |
| `v7_bot_32_ishtar_canyon_recompose_bold.jpg` | bot | recompose | 8.78 | 8.74 | 9.0 | 9.1 | 8.4 | 8.3 | 8.9 |

## Baseline detail

- `style_ref_01_night_city.png` (night_city) total=**6.95** mean=6.98 dims={'composition': 8.0, 'lighting_color': 7.2, 'perspective_anatomy': 6.7, 'texture_detail': 5.9, 'spec_style': 7.1}
  - The rooftop silhouette and central avenue create a strong sense of scale and a clear focal path. The cool atmosphere and scattered warm lights work well, but the city becomes indistinct at this resolution, and the figure
- `style_ref_02_pastel_sketch.png` (pastel_sketch) total=**7.3** mean=7.36 dims={'composition': 7.6, 'lighting_color': 7.1, 'perspective_anatomy': 6.8, 'texture_detail': 7.5, 'spec_style': 7.8}
  - The seated pose and red hoodie create a clear focal point, and the grainy pastel marks feel intentional rather than blurred. Color harmony and style are strong, though the lighting is fairly flat and the hand and shoe lo
- `style_ref_03_sunlit_portrait.png` (sunlit_portrait) total=**7.69** mean=7.64 dims={'composition': 7.6, 'lighting_color': 8.2, 'perspective_anatomy': 7.5, 'texture_detail': 7.1, 'spec_style': 7.8}
  - The centered portrait has a clear focal point, and the warm sunlight against the muted floral background creates a strong mood. Hair strands and fabric folds add interest, but the facial detail is soft—especially on the 
- `web_ref_01_concept_ishtar.png` (ishtar_canyon) total=**7.49** mean=7.52 dims={'composition': 7.6, 'lighting_color': 7.4, 'perspective_anatomy': 7.1, 'texture_detail': 7.7, 'spec_style': 7.8}
  - The steep overhead framing and converging walls create a compelling sense of depth, though the crowded center makes the focal point hard to read. Warm stone and cool shadows work well together; expressive linework gives 

## Full table

See `vlm_absolute_5d_v7.csv` and `generated_v7/vlm_absolute_5d_v7.json`.

## Files

- Desktop report: `docs/vlm_absolute_5d_v7_report.md`
- Desktop JSON: `generated_v7/vlm_absolute_5d_v7.json`
- Desktop CSV: `docs/vlm_absolute_5d_v7.csv`
- Scorer script (box): `/workspace/pmem-art-v7-vlm/vlm_absolute_5d_scorer.py`
