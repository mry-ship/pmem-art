# Final 3-Round Grok Optimize Synthesis & Permanent Policy

**Timezone:** Asia/Shanghai · **Written:** 2026-10-27 05:14 Asia/Shanghai  
**Runs:** Round1=`grok_v2` (mean **8.394**) · Round2=`grok_v3` (**8.371**) · Round3=`grok_v4` (**8.341**)  
**Best-of showcase:** `generated_v8_20_skill_grok_best/` mean **8.504** (sources: {'v2': 12, 'v4': 2, 'v3': 6})

## Trajectory

```
v1 8.286 ──(+0.108)──► R1/v2 8.394 ──(−0.023)──► R2/v3 8.371 ──(−0.030)──► R3/v4 8.341
                                                      ▲
                                         best-of pick ──► 8.504
```

Offline Absolute-5D + anat prior=7.0 caps practical totals ≈8.8. Policy churn after R1 moved dims around (texture↔lighting↔spec) but did **not** raise the mean. Further mean gains need **VLM anatomy** or a stronger generator, not more prompt locks.

## What worked (keep permanently)

| lever | evidence | keep? |
|---|---|---|
| `FORCE_REF_IF_TOTAL_LT=8.2` + no weak-pad chain | R1 bug fixed; stopped alley/melt amplification | **YES** |
| `SCENE_LOCK_ISHTAR` (eye-level terrace + 3-arch + dragon) | No top-down alley collapse in R2/R3 | **YES** |
| `TEXTURE_MATERIAL_LOCK` | R2 texture +0.273 (peak) | **YES** |
| `LIGHTING_NIGHT_LOCK` | R3 night winners +0.46/+0.48; light dim recovered | **YES** |
| `CONTACT_LOCK_NIGHT` | Contact language present; mild help | **YES** (cheap) |
| `SPEC_MEDIUM_LOCK` (non-bold + style_ref pad) | Reduces accidental medium swap | **YES** |
| `EARLY_STOP_R1_GE=8.5` (not 8.2) | R1 saved gens on strong starts; 8.2 over-froze mid pack | **YES @ 8.5** |
| Soften recompose (SOFT_RECOMPOSE) | Mild crop > hard FOV jump | **YES** |
| Anatomy + micro-detail locks on every prompt | Hygiene; no harm under offline | **YES** |
| Priority worst-first | Focused gen budget | **YES** |
| Versioned out dirs (`grok_vN`) | Safe rollback / best-of | **YES** |

## What didn’t work (drop or narrow)

| lever / idea | evidence | action |
|---|---|---|
| **Bold + source style_ref pad** | R2 bot_16 −0.54 (pastel pad vs pop) | **NEVER pad bold with incompatible style_ref** |
| **Bold fully padless as default regen** | R3 bot_24 −0.75, 08 −0.35, 32 −0.21 | Prefer **compatible medium pad** OR accept one-shot bold and early-stop; don’t burn 3 rounds padless |
| Strip-only `风格圣经跳变` → soft accent | Spec still declined; jump intent diluted | Keep strip for non-bold; for true style_jump use explicit target-medium block + optional *target* ref |
| “Keep identical composition” on recompose | Fought mild-crop (R2 bot_15) | **Skip on recompose/bold** (keep on low/med/high fix) |
| Lowering early-stop to 8.2 | Froze 11/20; blocked texture compounding | Restore **8.5**; only use 8.2 under tight quota |
| Expecting offline anat to move | Always 7.0 | Don’t spend rounds on anat prompts under offline |
| Full 20 × 3-round policy re-roll every time | Variance > signal after R1 | After a good R1 baseline, **patch only WORST8** |

## Recommended permanent policy (Grok GenerateImage converge)

```
DEFAULT_OUT = generated_v8_20_skill_grok_<version>
max_rounds = 3
anat_gate = 7.0          # offline; raise when VLM returns
score_backend = offline_absolute_5d | vlm when quota
EARLY_STOP_R1_GE = 8.5
FORCE_REF_IF_TOTAL_LT = 8.2
FORCE_REF_PAD_IF_R1_GE = 8.2   # snap to style_ref after strong R1 (non-bold)
SCENE_LOCK_ISHTAR = on
TEXTURE_MATERIAL_LOCK = on
LIGHTING_NIGHT_LOCK = on      # night_city only
CONTACT_LOCK_NIGHT = on
SPEC_MEDIUM_LOCK = on         # non-bold + style_ref pad
SOFT_RECOMPOSE / SOFT_BOLD = on
IDENTICAL_COMP_LOCK = low/medium/high only (NOT recompose/bold)

pad policy:
  - low/medium/high/recompose: style_ref or web_ref when total>=8.2 else force style_ref
  - recompose_bold / style_jump: pad_src=None OR a *target-medium* ref (never source style_ref)
  - never chain a gen with total < 8.2 as next pad

priority: worst-first (prior round totals)
concurrency: <=4
AR + style_refs: preserved per bot contract
```

### Operating loop (efficient)

1. Run full 20 once under permanent policy → freeze as baseline.  
2. Score offline (or VLM if quota).  
3. Re-gen **only WORST8** (and any scene-drift cases) with targeted locks — do not re-roll winners.  
4. Best-of merge into showcase.  
5. If mean still <9.0 and anat stuck: **wait for VLM** rather than more prompt engineering.

## Artifacts

| path | role |
|---|---|
| `generated_v8_20_skill_grok_v2/` | Round1 + ROUND1_OPTIMIZE_SUMMARY.md |
| `generated_v8_20_skill_grok_v3/` | Round2 + ROUND2_OPTIMIZE_SUMMARY.md |
| `generated_v8_20_skill_grok_v4/` | Round3 + ROUND3_OPTIMIZE_SUMMARY.md |
| `generated_v8_20_skill_grok_best/` | Best-of R1–R3 images + scores (showcase source) |
| `scripts/run_v8_20_skill_converge_grok.py` | Policy script (baks `_bak_v1/_v2/_v3`) |
| v1 dir | Preserved untouched |

## Bottom line

R1 levers (+force-ref / early-stop / soft recompose) delivered the only durable mean lift (+0.108). R2/R3 traded texture ↔ lighting ↔ spec without net gain; bold padless fixed medium fights but hurt totals. **Permanent policy = R1 base + R2 weak-pad/scene/texture locks + R3 night lighting + bold never pads with source style_ref; early-stop 8.5; patch WORST8 only; best-of for showcase.** Ceiling break needs VLM anatomy, not round 4 of the same offline loop.
