---
id: 01ART005ASTRARECIPE
module: character.Astra
entity: CostumeDesign
kind: recipe
status: active
note_date: '2026-10-22'
verified: '2026-10-24'
author: AI美术工程·陈默
summary: 阿斯特拉标准生图配方 v3：Flux.1-dev + eastern_celadon_astra_v3(0.85) + Seed 42819204
verify: 在 ComfyUI 加载 workflows/comfyui_astra_portrait_v3.json 直出，角色面部与服饰还原度 > 95%
applies: 生成阿斯特拉新动作、剧情半身像、皮肤换装底图
palette: ["#0F172A", "#F4F1EA", "#2DD4BF", "#F59E0B", "#E2E8F0"]
ai_params:
  model: "flux1-dev-fp8.safetensors"
  loras:
    - "eastern_celadon_astra_v3.safetensors:0.85"
    - "cel_shaded_ink_gold_v2.safetensors:0.45"
  sampler: "euler / beta / 28 steps / CFG 3.5"
  seed: 42819204
  controlnet: "openpose_full (0.72)"
  workflow: "workflows/comfyui_astra_portrait_v3.json"
  prompt: "1girl, solo, astra_astromancer, 7.5 heads tall, slender, silver white hair (#E2E8F0), golden brass astrolabe monocle on left eye with glowing cross star, right eye deep teal, deep slate outer cloak (#0F172A) with amber gold trim (#F59E0B), warm ivory inner tunic (#F4F1EA), celadon jade waist pendant (#2DD4BF), floating astronomical ring halo behind back, clean gold-ink lineart, cel-shaded painterly, transparent background"
  negative_prompt: "chibi, loli, 5 heads tall, neon magenta, cyberpunk, purple hair, monocle on right eye, दोनों eyes normal, white background, blurry edge, extra fingers, bad hands"
assets:
  - path: assets/character/astra_standing_v3.png
    role: approved
    caption: "使用本配方 v3 直出并经 RMBG-2.0 去背的标准立绘"
    sha256_16: 9c771d1f63976fb6
anchors:
  - workflows/comfyui_astra_portrait_v3.json
  - assets/character/astra_standing_v3.png
---
**【已验证可复现 AI 生产配方】**
- **核心触发词**：`astra_astromancer, golden brass astrolabe monocle on left eye, celadon jade waist pendant`。
- **LoRA 权重经验**：`eastern_celadon_astra_v3` 权重必须锁定在 `0.80 ~ 0.85`；超过 `0.95` 会导致衣褶高光过曝硬化，低于 `0.70` 会丢失左眼星盘义眼的十字刻度细节。
- **后处理节点**：已在 `workflows/comfyui_astra_portrait_v3.json` 尾部串联 `RMBG-2.0` + `Alpha-Premultiply-4px-Defringe` 节点，切勿手动旁路。
