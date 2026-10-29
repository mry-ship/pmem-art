# Round 1 Optimize Summary (Grok v2)

**Folder:** `generated_v8_20_skill_grok_v2/`  
**Timezone:** Asia/Shanghai  
**Status:** complete — 20/20 bots scored offline Absolute-5D

## Scores vs prior

| run | mean | min | max | n≥9.60 |
|---|---|---|---|---|
| Grok v1 (`generated_v8_20_skill_grok`) | **8.286** | — | — | 0 |
| **Round 1 / Grok v2** | **8.394** (+0.108) | 7.94 | 8.80 | 0 |
| gpt-image v2fix (ref) | 8.94 | — | — | — |
| oct26 backup (ref) | 9.14 | — | — | — |

- early-stop R1≥8.5: **5** bots (24,16,32,07,12)
- max_rounds (3): **15** bots
- anat gate: offline prior=7.0 treated as N/A → anat_ok=score_ok

## Dim means (offline Absolute-5D)

| dim | mean | note |
|---|---|---|
| composition | ~9.13 | strong |
| lighting | ~8.74 | ok |
| perspective_anatomy | **7.00** | offline prior stuck — **cannot move totals via anatomy lever** |
| texture_detail | **~7.34** | **real bottleneck** |
| spec_style | ~9.03 | strong |

## What changed this round (levers applied)

1. `FORCE_REF_PAD_IF_R1_GE=8.2` — snap pad to style_ref after a strong R1  
2. `EARLY_STOP_R1_GE=8.5` — stop if R1 already good  
3. Soften recompose / bold (SOFT_RECOMPOSE / SOFT_BOLD)  
4. Anatomy + micro-detail locks on every prompt  
5. DEFAULT_OUT → `grok_v2` (v1 preserved)

## Reverse-analysis — defects & levers

### Critical pad bug
On R1, `improved=True` always → auto pad chained the **first (often weak) gen** as R2/R3 pad when total < 8.2. That amplified scene drift (esp. ishtar → top-down alley) and plastic melt instead of recovering from style_ref.

### Scene drift (ishtar_canyon)
Bots 30 / 26 / 32 / others with web_ref often collapsed to top-down alley / courtyard shaft instead of eye-level terrace + three-arch bridge + flying dragon.

### Texture / material mush
texture_detail ~7.34: tile noise, melted paint smears, weak material edges (stone vs cloth vs scale). Offline anat locked at 7.0 so **texture is the only movable Absolute-5D lever**.

### Contact / join issues (night_city)
Floating feet / weak wrist-hilt continuity on swordsman scenes.

### Soften incomplete
Some “跳变” language still present in base compose; SOFT_* appended but did not fully neutralize identity jumps.

## Worst / best (Round 1)

**WORST5:** bot_30 7.94 · bot_02 7.98 · bot_04 8.17 · bot_18 8.20 · bot_26 8.24  
**BEST:** bot_24 / bot_15 8.80 · bot_12 8.63 · bot_32 8.60 · bot_07 8.56

## Round 2 patches (applied → `grok_v3`)

1. **`FORCE_REF_IF_TOTAL_LT=8.2`** — if this round is weak, next pad = style_ref (stop chaining bad gens)  
2. **Auto pad only when total≥8.2 AND non-decreasing**  
3. **`SCENE_LOCK_ISHTAR`** — eye-level terrace + three-arch bridge + flying dragon; forbid top-down alley  
4. **ishtar always force style_ref pad**  
5. **`TEXTURE_MATERIAL_LOCK`** — distinct material edges; no tile noise / melt  
6. **`CONTACT_LOCK_NIGHT`** — foot-to-ridge contact shadow + wrist-hilt join  
7. Priority order = Round1 worst: 30→02→04→18→26→22→08→28  
8. DEFAULT_OUT → `generated_v8_20_skill_grok_v3`

## Next (Round 2 execution)

Init + concurrent GenerateImage (≤4) worst-first, aim full 20; score offline; write `ROUND2_OPTIMIZE_SUMMARY.md`.
