# Round 2 Optimize Summary (Grok v3)

**Folder:** `generated_v8_20_skill_grok_v3/`  
**Timezone:** Asia/Shanghai  
**Finished:** 2026-10-27 04:59 Asia/Shanghai  
**Status:** complete — 20/20 bots scored offline Absolute-5D

## Scores vs prior

| run | mean | min | max | n≥9.60 | Δ vs prior |
|---|---|---|---|---|---|
| Grok v1 | 8.286 | — | — | 0 | — |
| Round 1 / Grok v2 | **8.394** | 7.94 | 8.80 | 0 | +0.108 |
| **Round 2 / Grok v3** | **8.371** | 7.97 | 8.80 | 0 | **−0.023** |
| gpt-image v2fix (ref) | 8.94 | — | — | — | — |
| oct26 backup (ref) | 9.14 | — | — | — | — |

- early-stop R1≥8.5: **3** bots (07, 12, 20)
- max_rounds (3): **17** bots
- anat gate: offline prior=7.0 → anat_ok

## Dim means (offline Absolute-5D)

| dim | R1 (v2) | R2 (v3) | Δ | note |
|---|---|---|---|---|
| composition | 9.134 | **9.197** | +0.063 | still strong |
| lighting_color | 8.741 | 8.615 | −0.126 | night_city stuck ~7.1–7.5 |
| perspective_anatomy | 7.000 | 7.000 | 0 | offline prior — immovable |
| texture_detail | 7.338 | **7.611** | **+0.273** | TEXTURE_MATERIAL_LOCK worked |
| spec_style | 9.030 | 8.856 | −0.174 | bold/pastel fought style_ref pad |

## What changed this round (levers applied)

1. `FORCE_REF_IF_TOTAL_LT=8.2` — weak gens no longer chained as pad  
2. Auto pad only when total≥8.2 AND non-decreasing  
3. `SCENE_LOCK_ISHTAR` + ishtar always force web/style_ref pad  
4. `TEXTURE_MATERIAL_LOCK` + `CONTACT_LOCK_NIGHT`  
5. Priority = Round1 worst-first  
6. DEFAULT_OUT → `generated_v8_20_skill_grok_v3`

## Reverse-analysis — what worked / what didn’t

### Worked
- **Texture +0.27** — material lock reduced melt/tile noise (real bottleneck moved).
- **Ishtar scene lock** — eye-level terrace+bridge+dragon mostly held (no alley collapse like R1).
- **Weak-pad fix** — confirmed `next_pad=style_ref` after totals <8.2.
- Gains: bot_30 +0.30, bot_20 +0.29, bot_18/07 +0.24, bot_08 +0.21, bot_22 +0.20.

### Didn’t work / regressions
- **Mean −0.023** — texture gains wiped by lighting/spec drops.
- **Bold + source style_ref pad conflict** — bot_16 (pastel→pop) stuck spec=7.0 / total 7.99 (−0.54). Pad forces pastel medium while prompt asks 波普赛璐璐; `match style_ref` fights the jump.
- **“风格圣经跳变” still in compose** — SOFT_BOLD append didn’t strip the jump phrase.
- **“Keep identical composition” on recompose** — contradicts mild-crop recompose intent (bot_15 −0.37).
- **night_city lighting flat** — bot_06/02 stuck light=7.1; CONTACT lock didn’t lift lighting dim.
- Offline anat still locked at 7.0 → totals ceiling ~8.8 without VLM.

## Worst / best (Round 2)

**WORST8:** bot_06 7.97 · bot_02 7.98 · bot_16 7.99 · bot_26 8.08 · bot_04 8.17 · bot_10 8.22 · bot_30 8.24 · bot_28 8.37  
**BEST:** bot_07 / bot_24 8.80 · bot_12 / bot_20 8.63 · bot_08 8.48 · bot_14 / bot_22 8.45

## Round 3 patches (→ `grok_v4`)

1. **Bold/style_jump: do NOT pad with source style_ref** (empty pad / no match-style_ref clause) — stop medium fight  
2. **Strip `风格圣经跳变` / `跳变` → `温和媒介强调`** in compose_prompt_v2  
3. **Skip “Keep identical composition…” for recompose/bold** (keep for low/medium/high fix rounds)  
4. **`LIGHTING_NIGHT_LOCK`** — warm lantern volume + teal/orange collision; forbid flat charcoal underexposure  
5. **`SPEC_MEDIUM_LOCK`** for non-bold — preserve medium identity when pad is style_ref  
6. Priority = Round2 worst: 06→02→16→26→04→10→30→28  
7. DEFAULT_OUT → `generated_v8_20_skill_grok_v4`  
8. Keep texture / ishtar / weak-pad / early-stop levers

## Next

Init + concurrent GenerateImage (≤4) worst-first full 20; score offline; write `ROUND3_OPTIMIZE_SUMMARY.md` + final synthesis.
