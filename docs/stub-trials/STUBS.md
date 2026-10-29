# Stub candidates (official trial list) — NOT applied to skills

Experiment only. Stubs below are candidates to eventually live in skill LOCK / GenerateImage overlay language. This run tests them as prompt overlays only.

| Slot | Where it would live in skill | Arm | Stubs |
|---|---|---|---|
| **Clone · Icon** | Mode B icon LOCK / GenerateImage overlay | **A** baseline | current skill language only, no extra stubs |
| | | **B** trial | `chunky vinyl-toy plastic volumes` · `soft studio key from upper-left` · `clear thumbnail silhouette` · `NO jewelry product render` · `NO micro metal scratches` |
| **Clone · UI** | UI chrome LOCK | **A** baseline | current skill language only, no extra stubs |
| | | **B** trial | `dual-rim chrome: thick gold outer + distinct orange/amber inner bevel` · `edge-readable laminate` · `exact brief copy only` · `reward prop NO face` · `NO gold-only single rim` |
| **Clone · Char** | Character LOCK | **A** baseline | skill eye/body LOCK only |
| | | **B** trial | `TWO separate eye sockets` · `large iris fills most of oval + white sclera crescent + specular highlight` · `soft cheeks short limbs barrel torso` · `empty-hand T-pose with clothing badge preferred` · `NOT cyclops NOT black-dot pupils` |
| **Merge · Mode A** | Mode A GenerateImage stubs | **CONTROL** | mandatory: `vinyl toy merge icon` · `chibi proportions` · `soft rounded bevels` · `soft painted shadows` · `NO metal specular` · `NO photoreal` · `NO product photography` |
| | | **EXTRA** | CONTROL + `squishy chibi mass` · `pastel candy brand glue` · `NO catalog product lighting` |
| **Merge · Mode B** | Mode B medium match (with style_ref pad) | **CONTROL** | skill Mode B baseline (pad medium; new theme) |
| | | **EXTRA** | CONTROL + same EXTRA trio woven if they help medium without fighting pad |
| **Merge · Mode C** | Mode C curriculum (market ladder pad → new family) | **CONTROL** | skill Mode C baseline |
| | | **EXTRA** | CONTROL + same EXTRA trio |

## Protocol notes
- Same brief + same refs for CONTROL vs EXTRA (or A vs B).
- Score Absolute-5D ≥9.5 honestly (agent vision). Merge uses ladder 5D (2.5/2.5/2.0/1.5/1.5).
- Prefer 1 round each to save cost.
- Mode B/C always pads style/curriculum refs via `reference_image_paths`. Mode A never pads.
- **Weave stubs as prose** — bare bullet lists can print into the plate (seen on Icon B).
- Do **not** edit skills, workflows, or `/workspace/pmem-art` project files.

## Theme locks this trial
- **Char:** blacksmith · empty-hand T-pose · horseshoe chest pin · soft clay casual · pads `ref_char.png` + `ref_icon.png`
- **Merge (A/B/C):** beach-candy family L1–L8 = ball → flip-flops → bucket → shovel → snorkel → duck → umbrella → sandcastle
  - Mode B pad: `pmem-stability-v4/merge_toy3d_bakery/sheet.jpg`
  - Mode C pad: `pmem-stability-market/refs/ref_merge_sheet.jpg`
