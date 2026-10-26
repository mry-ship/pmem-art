# REPORT — pmem-merge-ladder stability triple

**Date:** 2026-10-26 (Asia/Shanghai)  
**Root:** `/workspace/pmem-stability-triple/merge/`  
**Market ref:** Merge Mansion Gardening Tools → `market_ref_sheet.jpg` (Mode C medium+grid only)  
**Method:** whole-sheet one-shot → component slice → Absolute-5D ≥9.6  
**Gate:** 3 consecutive NEW-domain OK ladders — **MET**

---

## Results

| Group | Domain | Class | Rounds | Result | Sheet |
|---|---|---|---|---|---|
| G1 | bakery utensils | category-swap | 1 | **OK** | `G1/sheet.jpg` |
| G2 | cleaning tools | category-swap | 3 | **OK** | `G2/sheet.jpg` (r03) |
| G3 | sports gear | category-swap | 1 | **OK** | `G3/sheet.jpg` |

Streak path: OK → OK → OK (G2 internal r01/r02 fails did not end the group; final group verdict OK keeps streak).

---

## Deliverables present
- `market_ref_sheet.jpg`
- `G1/` `G2/` `G3/` each with `sheet.jpg`, `L01`–`L08`, `SCORES.md`, `compare_to_market.jpg`, `LADDER_BIBLE.md`
- `STREAK.md` `LEARNINGS.md` `SKILL_WORKING.md` `REPORT.md`

---

## Generic skill patches for parent to fold into workflows `pmem-merge-ladder`

1. **Default whole-sheet** — generate L1…LN as one contact sheet; slice; score; prefer whole-sheet regen on any cell fail.
2. **Prompt locks** — exactly N numbered item nouns; one brand-glue sentence; one toy-3D medium lock; “no text/faces/Lv”; Mode C: “new family, do not copy ref motifs.”
3. **N-count gate** — connected-component count must equal N before PASS.
4. **Silhouette noun test** — names must imply thumbnail-unique outlines; add shape words when two domains share a form (whisk↔duster).
5. **Late-rung superclass ban** — L7/L8 must not be near-duplicate same superclass (two brooms); prefer subclass swap.
6. **Same-family mass jump** — mini vs large twin needs ≥~1.6× silhouette or clearly more parts.
7. **Accent glue** — multi-canonical-color domains lock shared accent/grip + medium, not forced mono body color.
8. **L8 = max parts or max mass.**
9. **Component-bbox slice** before scoring when equal-split bleeds.
10. **Honesty** — Read pixels; write five numbers; any cell <9.6 → group not OK.

Working copy with patches: `SKILL_WORKING.md` (do not confuse with live workflows skill until parent syncs).

---

## Honesty notes
- G1 L01 reads as scoop more than flat measuring spoon — still bakery-domain complete tool.
- G2 required two failed sheets before OK; failures produced the highest-value generic rules (N-count, silhouette nouns, superclass ban).
- G3 brand glue is accent-orange on handled gear; balls keep sport-canonical colors.
- No GitHub push performed.
