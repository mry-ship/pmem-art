# Round 3 Optimize Summary (Grok v4)

**Folder:** `generated_v8_20_skill_grok_v4/`  
**Timezone:** Asia/Shanghai  
**Finished:** 2026-10-27 05:14 Asia/Shanghai  
**Status:** complete — 20/20 bots scored offline Absolute-5D

## Scores vs prior

| run | mean | min | max | n≥9.60 | Δ vs prior |
|---|---|---|---|---|---|
| Grok v1 | 8.286 | — | — | 0 | — |
| Round 1 / Grok v2 | **8.394** | 7.94 | 8.80 | 0 | +0.108 |
| Round 2 / Grok v3 | **8.371** | 7.97 | 8.80 | 0 | −0.023 |
| **Round 3 / Grok v4** | **8.341** | 7.98 | 8.80 | 0 | **−0.030** |
| Best-of R1–R3 (showcase) | **8.504** | 7.98 | 8.80 | 0 | pick max per bot |
| gpt-image v2fix (ref) | 8.94 | — | — | — | — |
| oct26 backup (ref) | 9.14 | — | — | — | — |

- early-stop R1≥8.2 (label still `STOP_EARLY_R1_GE_8_5`): **11** bots
- max_rounds (3): **9** bots
- anat gate: offline prior=7.0 → anat_ok
- vs Round2: improved **4** · same **10** · regressed **6**

## Dim means (offline Absolute-5D)

| dim | R1 (v2) | R2 (v3) | R3 (v4) | Δ R2→R3 | note |
|---|---|---|---|---|---|
| composition | 9.134 | 9.197 | **9.197** | +0.000 | flat / strong |
| lighting_color | 8.741 | 8.615 | **8.813** | +0.198 | LIGHTING_NIGHT_LOCK recovered |
| perspective_anatomy | 7.000 | 7.000 | 7.000 | 0 | offline prior — immovable |
| texture_detail | 7.338 | **7.611** | 7.359 | -0.252 | R2 texture gains partially lost |
| spec_style | 9.03 | 8.856 | 8.74 | -0.116 | continued soft decline |

## What changed this round (levers applied)

1. **Bold/style_jump: pad_src=None** — no source style_ref pad; drop `match style_ref` clause
2. Strip `风格圣经跳变` / `跳变` → `温和媒介强调` in compose
3. Skip “Keep identical composition…” for recompose/bold
4. **`LIGHTING_NIGHT_LOCK`** — warm lantern volume + teal/orange collision; forbid flat charcoal
5. **`SPEC_MEDIUM_LOCK`** for non-bold — preserve medium when pad is style_ref
6. **`EARLY_STOP_R1_GE` lowered 8.5→8.2** mid-run (finish full 20 without burning gens)
7. Priority = Round2 worst: 06→02→16→26→04→10→30→28
8. DEFAULT_OUT → `generated_v8_20_skill_grok_v4`
9. Keep texture / ishtar / weak-pad / FORCE_REF_IF_TOTAL_LT levers

## Reverse-analysis — what worked / what didn’t

### Worked
- **Night lighting lock** — bot_04 **+0.46** (8.17→8.63), bot_06 **+0.48** (7.97→8.45); night_city lighting dim recovered to ~9.12 on winners.
- **Ishtar scene lock held** — bot_28 **+0.26** (8.37→8.63) early-stop; bot_31/32 kept terrace+bridge+dragon (no alley collapse).
- **Bold no-pad** — bot_16/08/24/32 generated without pastel/night style_ref fighting target medium (cyber/pop/anime/ukiyo-e readable).
- **Early-stop @8.2** — 11/20 froze strong R1 (07=8.8, 12=8.63, 28=8.63…) → saved gens; mean drag mostly from bold variance + sticky offline dims.

### Didn’t work / regressions
- **Mean −0.030 vs R2** (cumulative −0.053 vs R1). Policy patches did not lift the Absolute-5D ceiling.
- **Bold no-pad quality risk** — bot_24 8.80→8.05 (−0.75), bot_08 −0.35, bot_32 −0.21. Removing pad frees medium but loses composition/lighting anchor.
- **Texture slipped −0.252** — early-stop froze many R1s before texture lock could compound; bold gens also weaker on material edges.
- **Spec −0.116** — mild “温和媒介强调” still under-delivers vs style_ref match on non-bold; bold freestyle disperses style dim.
- **Offline anat=7.0 wall** — totals mathematically capped ~8.8 without VLM anatomy credit.
- **bot_16 only +0.06** after no-pad — recovered from R2 disaster (7.99) but still far below R1 8.53; style_jump remains hard for Grok without a *compatible* pad.

## Worst / best (Round 3)

**WORST8:** 02 7.98 · 16 8.05 · 24 8.05 · 26 8.08 · 08 8.13 · 10 8.22 · 15 8.22 · 32 8.22  
**BEST:** 07 8.8 · 04 8.63 · 12 8.63 · 28 8.63 · 20 8.49 · 06 8.45 · 14 8.45 · 18 8.44

## Per-bot Δ Round2 → Round3

| bot | R2 | R3 | Δ | best_r | case/scale |
|---|---|---|---|---|---|
| 24 | 8.8 | 8.05 | -0.75 | r3 | sunlit_portrait/recompose_bold |
| 08 | 8.48 | 8.13 | -0.35 | r3 | night_city/recompose_bold |
| 15 | 8.43 | 8.22 | -0.21 | r1 | pastel_sketch/recompose |
| 22 | 8.45 | 8.24 | -0.21 | r1 | sunlit_portrait/high_best |
| 32 | 8.43 | 8.22 | -0.21 | r1 | ishtar_canyon/recompose_bold |
| 20 | 8.63 | 8.49 | -0.14 | r1 | sunlit_portrait/medium_best |
| 02 | 7.98 | 7.98 | +0.00 | r1 | night_city/low_best |
| 07 | 8.8 | 8.8 | +0.00 | r1 | night_city/recompose |
| 10 | 8.22 | 8.22 | +0.00 | r2 | pastel_sketch/low_best |
| 12 | 8.63 | 8.63 | +0.00 | r1 | pastel_sketch/medium_best |
| 14 | 8.45 | 8.45 | +0.00 | r2 | pastel_sketch/high_best |
| 18 | 8.44 | 8.44 | +0.00 | r1 | sunlit_portrait/low_best |
| 23 | 8.43 | 8.43 | +0.00 | r1 | sunlit_portrait/recompose |
| 26 | 8.08 | 8.08 | +0.00 | r3 | ishtar_canyon/low_best |
| 30 | 8.24 | 8.24 | +0.00 | r1 | ishtar_canyon/high_best |
| 31 | 8.43 | 8.43 | +0.00 | r1 | ishtar_canyon/recompose |
| 16 | 7.99 | 8.05 | +0.06 | r1 | pastel_sketch/recompose_bold |
| 28 | 8.37 | 8.63 | +0.26 | r1 | ishtar_canyon/medium_best |
| 04 | 8.17 | 8.63 | +0.46 | r2 | night_city/medium_best |
| 06 | 7.97 | 8.45 | +0.48 | r2 | night_city/high_best |

## Next (post Round 3)

See `FINAL_3ROUND_SYNTHESIS_AND_POLICY.md` — recommended permanent policy + best-of showcase sync.
