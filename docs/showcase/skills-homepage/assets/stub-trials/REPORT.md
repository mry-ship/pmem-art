# Stub A/B trial REPORT — KEEP applied to skills

> **Applied 2026-10-27 Asia/Shanghai:** KEEP stubs from Summary table woven into `pmem-clone-image` + `pmem-merge-ladder` skills (prose overlays). Skills edited; this file is evidence.

Original run was experiment-only; KEEP phrases later shipped into project skills.

**Date:** 2026-10-27 Asia/Shanghai (CST)  
**Authorized by:** t59u / pt59u · t60u / pt60u (char + merge A/B/C expand)  
**Root:** `/workspace/pmem-stub-trials/`  
**Constraint honored:** did **not** edit skills, workflows, or `/workspace/pmem-art`.

Official stub table: `STUBS.md`.

**Prompting rule learned:** weave stubs as **prose**, never bare bullet checklists (Icon B once printed the list into the plate).

---

## Phase 1 — Clone Icon + UI (earlier)

### Icon — purple potion · pad `ref_booster_propeller.png` · black BG

| Arm | Path | Dims | Total | Gate |
|---|---|---|---|---|
| A | `icon/A/r1.jpg` | 构图9.7/光影9.6/透视9.7/质感9.5/风格9.6 | **9.63** | PASS |
| B | `icon/B/r1.jpg` | 构图9.7/光影9.7/透视9.7/质感9.7/风格9.7 | **9.70** | PASS |

dim4 B +0.2. Compare: `icon/compare_AB.jpg`

### UI — Bonus! / Extra moves +3 / Grab · scroll · pad `ref_ui.png` (edge-cropped)

| Arm | Path | Dims | Total | Gate |
|---|---|---|---|---|
| A | `ui/A/r1.jpg` | 构图9.6/光影9.5/透视9.6/质感9.1/风格9.5 | **9.49** | **FAIL** |
| B | `ui/B/r1.jpg` | 构图9.7/光影9.6/透视9.6/质感9.7/风格9.7 | **9.66** | PASS |

dim4 B +0.6 (mid-edge dual-rim). Compare: `ui/compare_AB.jpg`, `ui/compare_chrome_MR.jpg`

### Phase 1 stub recs (unchanged)
| Stub | Rec |
|---|---|
| Icon `chunky vinyl-toy…` / `soft studio key UL` / `NO jewelry` / `NO micro metal scratches` | **KEEP** |
| Icon `clear thumbnail silhouette` | **REWRITE** (already in skill) |
| UI `dual-rim gold+amber` / `edge-readable laminate` / `reward prop NO face` / `NO gold-only single rim` | **KEEP** (highest ROI) |
| UI `exact brief copy only` | **REWRITE** (overlap) |

---

## Phase 2 — Clone Char + Merge Mode A/B/C

### 3) Char — blacksmith · pads `ref_char.png` + `ref_icon.png`

| Arm | Path | Dims | Total | Gate |
|---|---|---|---|---|
| A | `char/A/r1.jpg` | 构图9.7/光影9.6/透视9.6/质感9.5/风格9.6 | **9.61** | PASS |
| B | `char/B/r1.jpg` | 构图9.7/光影9.6/透视9.7/质感9.5/风格9.7 | **9.65** | PASS |

Eye crops: `char/A/eyes/`, `char/B/eyes/` · Compare: `char/compare_AB.jpg`, `char/compare_eyes.jpg`

Both hold TWO sockets + iris + sclera + specular + empty T-pose + horseshoe. **B dim3 slightly clearer sclera crescent.**

#### Char stub recs
| Stub | Rec | Why |
|---|---|---|
| `TWO separate eye sockets` | **KEEP** | Hardens anti-cyclops; both arms OK, explicit phrase is cheap insurance |
| `large iris fills most of oval + white sclera crescent + specular highlight` | **KEEP** | B crop more readable; overlaps skill but prose package helps |
| `soft cheeks short limbs barrel torso` | **KEEP** | Aligns body LOCK; B slightly chunkier |
| `empty-hand T-pose with clothing badge preferred` | **KEEP** | Both held horseshoe + empty hands |
| `NOT cyclops NOT black-dot pupils` | **KEEP** | Negative pair; keep with iris positive |

---

### 4) Merge — beach-candy family L1–L8 (ball→flipflops→bucket→shovel→snorkel→duck→umbrella→sandcastle)

| Mode | Arm | Sheet | Min cell | Ladder |
|---|---|---|---|---|
| **A** (zero ref) | CONTROL | `merge/modeA/CONTROL/sheet_r1.jpg` | **9.7** | **PASS** |
| **A** | EXTRA | `merge/modeA/EXTRA/sheet_r1.jpg` | **9.8** | **PASS** |
| **B** (pad toy3d bakery sheet) | CONTROL | `merge/modeB/CONTROL/sheet_r1.jpg` | **8.7** | **FAIL** (L6 face) |
| **B** | EXTRA | `merge/modeB/EXTRA/sheet_r1.jpg` | **8.8** | **FAIL** (L6 face) |
| **C** (pad market garden ladder) | CONTROL | `merge/modeC/CONTROL/sheet_r1.jpg` | **8.6** | **FAIL** (L6 face) |
| **C** | EXTRA | `merge/modeC/EXTRA/sheet_r1.jpg` | **8.5** | **FAIL** (L6 face; duck silhouette drift) |

Compares: `merge/modeA|B|C/compare_CONTROL_vs_EXTRA.jpg`  
Pads documented: `merge/modeB/PAD.txt`, `merge/modeC/PAD.txt`  
Per-mode scores: `merge/modeA|B|C/SCORES.md`

**Shared failure (B/C):** L6 inflatable duck grew **black-dot eyes** (prop face) — d4 redline. Mode A CONTROL+EXTRA both kept duck **faceless**. EXTRA did **not** fix B/C faces; it did nudge candy/squishy plastic (Mode A lift; Mode B/C sandcastle less grit).

#### Merge EXTRA stub recs (per mode)
| Stub | Mode A | Mode B | Mode C |
|---|---|---|---|
| `squishy chibi mass` | **KEEP** | **REWRITE** — help medium only if paired with `props NO faces NO eyes` | **REWRITE** — same; alone insufficient |
| `pastel candy brand glue` | **KEEP** | **KEEP** (pastel held with pad) | **KEEP** (family glue OK) |
| `NO catalog product lighting` | **KEEP** | **KEEP** (mild grit reduced on EXTRA castle) | **KEEP** (EXTRA castle more molded-toy) |

**Rollup:** EXTRA trio is a **Mode A KEEP**. For Mode B/C treat as optional medium polish **only after** face redline is locked (`props NO faces` / `NO black-dot eyes on props`) — otherwise DROP as a standalone fix.

---

## Summary KEEP / DROP / REWRITE (all slots)

| Slot | KEEP | REWRITE | DROP / DEFER |
|---|---|---|---|
| Icon | vinyl volumes; UL key; NO jewelry; NO micro scratches | clear thumbnail silhouette | — |
| UI | dual-rim gold+amber; edge-readable laminate; reward NO face; NO gold-only single rim | exact brief copy only | — |
| Char | all five B stubs | — | — |
| Merge EXTRA | all three for **Mode A**; candy glue + NO catalog lighting also OK on B/C | squishy chibi mass on B/C → add face ban | do not ship EXTRA alone as B/C face fix |

## File index (Phase 2 adds)
```
char/A|B/{r1.jpg,PROMPT.txt,SCORES.md,eyes/*}
char/compare_AB.jpg, compare_eyes.jpg, COMPARE.md
merge/modeA|B|C/CONTROL|EXTRA/{sheet_r1.jpg,cells/L01..L08.png}
merge/modeA|B|C/{SCORES.md,compare_CONTROL_vs_EXTRA.jpg}
merge/modeB/PAD.txt, merge/modeC/PAD.txt
```
