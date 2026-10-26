# REPORT — pmem-clone-image stability loop

**Result: 3 consecutive OK groups (G1 → G2 → G3).** Loop complete.

## Definition met
Each OK group = Mode B icon + char + UI, every asset Absolute-5D ≥9.6, every gen used real `reference_image_paths` (no fake pairs). New subjects each group.

## Group summary

### G1 (streak 1)
| Asset | Subject | Winner | Score |
|-------|---------|--------|-------|
| Icon | Emerald gem | r01 | 9.6 |
| Char | Baker + rolling pin badge | r03 | 9.6 |
| UI | Bonus! / Free scroll reward | r02 | 9.7 |

### G2 (streak 2)
| Asset | Subject | Winner | Score |
|-------|---------|--------|-------|
| Icon | Purple potion | r01 | 9.7 |
| Char | Gardener + sunflower chest pin | r07 | 9.6 |
| UI | Lucky! / coins | r01 | 9.7 |

### G3 (streak 3)
| Asset | Subject | Winner | Score |
|-------|---------|--------|-------|
| Icon | Scroll + gold band + red wax seal | r01 | 9.7 |
| Char | Blacksmith + horseshoe pin (empty hands) | r02 | 9.6 |
| UI | Jackpot! / Win a rare gem / Open | r02 | 9.6 |

## Failures that became generic rules
1. **Char prop scale brittleness** (G2 r01–r05 watering can / pot too tiny) → prefer empty-handed T-pose + clothing badge / belt / ground prop (rules 12–13).
2. **Iris shrink / black-dot eyes** → aux-pad icon iris + absolute iris recipe (rule 9); G3 r01 cyclops = hard redline fail, fixed r02 with explicit TWO-eyes ban.
3. **UI chrome collapse to gold-only** (G3 r01) → edge-crop verify dual gold outer + orange/amber inner (rule 11); refine with chrome-first prompt.
4. **Pad policy when scale is the bug** → drop prior result pad; keep style-ref only so proportion errors don't lock in.

## Artifacts
`/workspace/pmem-stability-triple/clone/`
- `G1/` `G2/` `G3/` — each with icon/char/ui (source, result png, compare, SCORES)
- `STREAK.md` — live status (final streak=3)
- `LEARNINGS.md` — generic failure→rule patches
- `SKILL_WORKING.md` — skill + reverse-engineered generics
- `REPORT.md` — this file

No GitHub push.
