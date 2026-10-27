---
name: pmem-lens-propose
description: Use when the user drops a reference image (or names a style_ref) and wants several concrete lens / lighting / prop packages to pick from before generating—V2-style showcase language, choose then generate.
---

# pmem-lens-propose

这不是单独技能。只有玩家明确要几套机位时，才走 `/pmem-draw` 里的镜头包合同。没人要镜头，不要因为 `high` 或 `recompose` 打开这一页。点选前不生图。

Off-line **lens pack** step before converge / edits. Look at a reference image, propose several concrete cinematic packages (camera, light, props, forbids), let the user pick, then hand the chosen pack into goal / recompose_dir / best_direction—do **not** invent Absolute-5D scores.

## When

- 玩家明确要几套机位、镜头或光来挑。
- 不是 `high` / `recompose` 的默认前置。没人要镜头就继续当前这一支。
- 换题材锁画风走 `/pmem-draw` 的克隆合同，不走这里。
- 只审图不走这里。

## Inputs

- Required: one reference image (any subject). Known slugs (`night_city` / `pastel_sketch` / `sunlit_portrait` / `ishtar_canyon`) are optional shortcuts only — do not refuse other images.
- Optional: target scales (`low` `medium` `high` `recompose` `recompose_bold`), count of packs (default **4**), language (default zh + short en keywords), identity lock notes from the user.

## Steps

1. **Resolve image**  
   Open/read the reference. Note aspect, subject identity (gender/species/age anchors), medium/palette, current camera. Do not invent props already absent as if they were in the ref.

2. **Debrief (short)**  
   One short paragraph: what must stay (identity + medium) vs what may leap (camera / light / narrative ornaments by scale).

3. **Propose N packs** (default 4)  
   Each pack is a pickable card with fixed fields:
   - `id`: A/B/C/…
   - `scale_fit`: which scales it suits (e.g. high, or recompose-only)
   - `title`: 6–12字
   - `camera`: concrete shot (height, angle, framing)—no vague「更好构图」
   - `light`: concrete light (direction, color clash, volume)
   - `props`: 1–3 style-in ornaments (may add for high+; must not swap identity)
   - `forbid`: hard no (old camera DNA, identity swap, empty boilerplate)
   - `goal_zh`: one goal line ready for `bot_tasks` / converge `--goal`
   - `recompose_dir`: only if scale_fit includes recompose; else empty
   - `best_direction`: one overlay line like `最优方向：…`

   Rules for pack quality:
   - Specific nouns (孔明灯级), not「加强氛围」「提升质感」.
   - At least **one** pack keeps near-ref camera (high polish); at least **one** is a true recompose camera change.
   - Bold/style_jump packs must say silhouette-only + new style bible.
   - Never attach fake scores or STOP claims.

4. **User picks**  
   Send a widget (multiSelect if they may merge). Values must read like natural replies (e.g. `选 A 孔明灯体积光`). Do not generate images in this step.

5. **Materialize**  
   After pick:
   - Write/update the chosen fields into the task source they are using (`goal`, `gen_description`, `recompose_dir`, `best_prompts` overlay)—or print a ready `converge start …` command block.
   - Confirm identity locks still present.
   - Ask once whether to start generate/converge now; only then run edits.

6. **Optional contrast**  
   If they ask「和 V2 比」, map which pack is closest to known V2 showcase lenses for that ref—still no scripted scores.

## Output shape (chat)

Lead with the debrief (2–3 sentences). Then one short block per pack (title + camera/light/props/forbid + goal). End with the pick widget—not a long essay.

## Anti-patterns

- Dumping generic `best_direction_hint` scale boilerplate as a pack.
- Proposing packs then auto-generating without a pick.
- Treating this skill as a scorer or as pmem-clone-image.
- Chaining edit-from-previous-round here; pad policy belongs to the converge runner.
