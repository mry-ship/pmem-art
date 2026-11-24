# -*- coding: utf-8 -*-
"""Single source of numeric defaults for layer-split local pipeline.

Keep in sync with `.cursor/skills/pmem-layer-split/SKILL.md` §闸门与尺寸.
Do NOT invent extra stop lines for converge (9.5) — this skill is not converge.
"""

# gpt-image-2.5 / apikey-image allowed --size only
ALLOWED_SIZES = ("1024x1024", "1024x1536", "1536x1024")

# pixel_aspect = (norm_w / norm_h) * (canvas_W / canvas_H)
SIZE_BUCKETS = (
    (0.85, "1024x1536"),  # pa < 0.85 → portrait
    (1.20, "1024x1024"),  # 0.85–1.2 → square
    (None, "1536x1024"),  # pa > 1.2 → landscape
)

# crop area fraction of full canvas → --quality (size still from buckets)
QUALITY_BY_AREA = (
    (0.04, "medium"),  # tiny props
    (0.12, "high"),
    (None, "high"),  # large / bg if ever isolated
)

GATE = {
    # |log(spr_asp / box_px_asp)| — aspect mismatch
    "asp_err_max": 0.18,
    # placed_area / box_area after contain
    "fill_min": 0.72,
    "fill_max": 1.08,
    # mean alpha of isolated PNG (0–1); too high ≈ opaque tile / bleed
    "alpha_mean_max": 0.92,
    # too empty
    "alpha_mean_min": 0.02,
    # template-match score (cv2 TM_CCOEFF_NORMED) below → calibrate_fail
    "match_score_min": 0.55,
    # sprite vs crop feature lock (masked color/luma/hist under alpha); catches redesigns
    # 0.42 let viking redesigns (tent/cabin ≈0.59–0.67) slip — raise floor; Agent visual §4.1 still required
    "feat_match_min": 0.55,
    # fraction of opaque alpha mass on outer border — high ⇒ clipped/incomplete part
    "edge_clip_max": 0.018,
    "edge_clip_border_px": 2,
    # longest flush run on the CONTENT bbox edge, as a fraction of that side.
    # A straight cut through the subject (pond sliced on the left) stays high
    # after letterbox pads the file border, so edge_clip misses it.
    "content_cut_max": 0.32,
    "content_cut_border_px": 3,
    # Rows of the content box's left or right edge that touch that edge.
    # A 249px cap slice was only 0.23 of a tall bbox, so the ratio alone passed.
    # A whole round edge can itself touch its box for about 70 rows; sliced caps were 169+.
    "side_cut_px": 120,
    # Opposite transparent gaps of the content box inside the footprint frame.
    # One side empty is a removed neighbor. Both sides empty means the subject
    # was shrunk into the middle of the picture band.
    # Both ends must clear this. A mushroom cluster at 0.15/0.14 still fills its crop;
    # a mole floating at 0.36/0.30 does not.
    "inner_gap_max": 0.15,
    # Share of the subject's opaque pixels that sit outside the picture band.
    # A thin tip may cross. A subject drawn into the pad (pond rim pushed out
    # until contain-fit shrinks the whole layer) is above this.
    "engine_band_bleed_max": 0.12,
    # bg vs ref NCC inside prop footprints — high ⇒ characters/props still baked into empty stage
    # 0.62 still let soft residue / footprint stains slip on busy camps — tighten for empty-stage quality
    "bg_bake_max": 0.58,
    # bg plate aspect vs canvas after normalize (diagnostic hard fail if still stretched)
    "bg_stretch_err_max": 0.12,
    # Diagnostic only — do NOT mark dirty / do NOT redraw for this.
    # Same object sitting a bit small in the footprint is fixed by placement.
    # Redraw is for a different silhouette, missing parts, clipped edges, or baked neighbors.
    # 0.75 remains the note threshold (lantern/heroine ≈0.66 is worth a look, not a re-roll).
    "scale_mul_min": 0.75,
    # whole-compose ghost QA
    "ghost_mae_warn": 28.0,
    "ghost_mae_fail": 48.0,
    # per-layer footprint MAE (qa) → dirty feedback into status (gate ok ≠ restore ok)
    "layer_ghost_mae_max": 52.0,
    # per-id retry budget
    "max_retries": 2,
}

# Norm-space pads for boxes / isolate crops (full-frame fraction).
# Player contract: boxes must fully enclose the subject — never send clipped tiles to the model.
# Agent drafts already use ≥0.08 tip pad. Setup used to add +0.10 then isolate +0.08 →
# footprints ballooned (heroine/lantern scale_mul≪0.82, ghost hot). Keep a SMALL setup
# safety expand only; completeness still relies on Agent draft + edge_clip gate.
CROP_PAD_PLAN = 0.05  # setup safety expand (Agent draft should already cover tips)
CROP_PAD_PLAN_SOFT = 0.10  # fur / flame / soft edges / spear tips (Agent draft hint)
CROP_PAD_TIGHTEN = 0.06  # silhouette tighten margin when bg-diff usable
CROP_PAD_ISOLATE_EXTRA = 0.05  # expand beyond truth when exporting isolate crop PNG
CROP_PAD_EDGE_GROW = 0.03  # reserved helper; not used in default setup loop
CROP_PAD_EDGE_GROW_MAX = 0.10
# Dual-pad isolate: primary = generous crop; secondary = full-scene highlight context
ISOLATE_USE_CONTEXT_PAD = True

# {shadow_rule} filled from layer.grounded (see isolate.shadow_rule_for)
# Crop pixels = GROUND TRUTH for LOOK. KEEP/REMOVE are short slot tags only — never invent over the crop.
# Position and span stay inside the crop frame. Compose pastes that frame; it does not recenter.
ISOLATE_PROMPT = """STRICT ISOLATE — LOCK LOOK to crop pixels for restore-quality layer split (not a redesign).
Transparent background if the engine supports alpha; otherwise solid pure black isolation plate (no gray, no scene).
References: (1) PRIMARY = this subject's crop, already contain-fitted on the engine canvas. Black bars are empty pad, not part of the scene. The picture inside the bars is the pixel ground truth for identity, pose, and materials.
(2) OPTIONAL SECOND = full scene with THIS subject's box highlighted (outside dimmed) — use only for lighting/style/context continuity; do NOT copy neighbors or the whole scene.
KEEP text only NAMES the slot — do NOT invent details from KEEP alone; match what is visible in the primary crop.
Hard locks (appearance must match the primary crop):
1) SAME camera angle / perspective / FOV as the crop — do NOT change viewpoint
2) SAME composition pose and orientation / silhouette shape as the crop
3) SAME key features, materials, colors, part inventory as visible on the subject in the crop
4) SAME art style as the crop (line, shading, saturation) — extract/split only, do not restyle
5) WHOLE-SUBJECT COMPLETENESS — do NOT clip caps, curls, rims, bells, spear tips, flame tips, hanging charms, cloak hems, limbs, poles, or roof peaks. Keep the margin the subject already has inside the crop. If the reference shows empty crop between a tip, curl, vine, cap, or rim and the crop edge, keep that same empty gap. Do NOT slide that part onto the picture-band edge. Black bars outside the picture band are empty padding and must stay empty. Do NOT stretch any part out to those bars. Do NOT pull the subject into a smaller product shot. A straight cut through a rounded part is FAIL.
6) NO REDESIGN / NO SPECIES CHANGE — silhouette family must match the crop (A-frame tent stays A-frame, not a draped pavilion; cabin stays the crop viewpoint, not a new frontal house; same spear count / shield layout). A complete but different prop = FAIL.
7) SAME SCENE LIGHTING FAMILY as the crop/context — keep warm fire/lantern bounce AND cool moon/sky rim if both are visible on the subject; do NOT relight into neutral studio softbox or product-shot even lighting on a black void.
8) POSITION AND SPAN LOCK — the picture band IS the footprint. Keep the subject in the same place and at the same size as in that band. This is an in-place edit: delete the listed neighbors and turn the rest transparent. Do NOT redraw, rescale, or move parts that are already fully visible. Compose maps the picture band onto the footprint and clips anything drawn in the black bars. It will not scale the subject back.
{frame_rule}
Edit in place. Delete everything that is not the listed subject. If a neighbor occludes the subject in the crop, complete ONLY the hidden part, inside the same span — do NOT redraw the visible part, and do NOT invent a different object, gender, pose, prop layout, roof type, or species.
If the crop already shows the full silhouette, keep that exact span inside the picture band. Do not move a side-sitting subject to the center, and do not shorten a part so it no longer spans the same fraction of the band. A tidier product-shot is FAIL.
If occlusion hides MOST of the subject, Agent should have tightened neighbor boxes or merged slots first — still do NOT invent a different prop species.
Natural proportions — do NOT squash or stretch.
{shadow_rule}
Contact/cast shadow under the subject IS PART OF the sprite when grounded — keep it.
No huge fake oval studio drop-shadow. No full dirt/snow/grass ground-plane carpet.
KEEP ONLY (slot tag): {keep}
MUST REMOVE: {remove}, neighbors, ground fill carpet, sky, unrelated furniture.
Match crop art style exactly. No redesign.
"""

# Background must be a sharp empty-stage plate (default path = image2.5, not local dig).
# {aspect_rule} injected when engine --size aspect ≠ canvas aspect (pillarbox / letterbox, never squash).
BG_ISOLATE_PROMPT = """EMPTY STAGE BACKGROUND — LOCK camera and landscape to the crop (restore-quality empty plate).
The full-scene crop is GROUND TRUTH for proportions, horizon, distant tree count/placement, snow/grass pattern, sky/aurora/moon, and art style.
KEEP ONLY (slot tag): {keep}
MUST REMOVE: {remove}, every character, every prop, buildings/furniture listed — AND also remove their contact shadows, fire-pit stains, footprint dark patches, and warm glow pools that only exist because those props were there.
Hard locks:
1) SAME camera angle / FOV — do NOT reframe
2) SAME ground/horizon/distant-tree layout and proportions — distant pines stay FAR, SMALL, and recessed like the crop silhouettes; do NOT invent large midground hero trees flanking the clearing, new paths, or a rearranged forest. Midground hero trees/rocks that are their OWN modules are removed here and live on those layers — do not bake them into bg AND do not leave dark stump scars.
3) SAME art style and scenic lighting family (cool night / warm ambient OK) — but NO baked prop silhouettes
4) ZERO prop residue — no ghost bodies, tents, racks, pots, banners, half-erased furniture, or dark oval stains where props stood
5) HOLE FILL — fill only the hole a removed prop left, by continuing the ground already visible beside that hole. Keep the crop's flowers, scenic light, and open lawn pattern everywhere else. Do not repaint a new meadow or move those flowers. No muddy inpaint blobs, no swiss-cheese holes, no scar rings
6) Prop shadows travel WITH prop layers — empty stage must NOT keep those ground shadows
7) Open empty clearing in the middle must remain OPEN — do not refill it with trees/rocks/props to "look pretty"
{aspect_rule}
Sharp clean opaque scenic fill. Empty stage must still match the crop's empty landscape identity when all listed subjects are gone.
"""


def engine_content_band(
    content_w: int, content_h: int, engine_w: int, engine_h: int
) -> tuple[float, float, float, float]:
    """Fractions of the engine frame that are empty pad around the crop.

    Returns (left, top, right, bottom). The crop is contain-fitted, never
    squashed. A taller crop gets left/right bars; a wider crop gets top/bottom
    bars. Those bars are the only pad. They are not a second margin inside
    the picture.
    """
    content_asp = content_w / max(1, content_h)
    engine_asp = engine_w / max(1, engine_h)
    if abs(content_asp - engine_asp) / max(engine_asp, 1e-6) < 0.02:
        return (0.0, 0.0, 0.0, 0.0)
    if content_asp < engine_asp:
        side = (1.0 - content_asp / engine_asp) / 2.0
        return (side, 0.0, side, 0.0)
    vert = (1.0 - engine_asp / content_asp) / 2.0
    return (0.0, vert, 0.0, vert)


def frame_rule(size: str, band: tuple[float, float, float, float]) -> str:
    """Tell a prop isolate which part of the engine canvas is the crop."""
    left, top, right, bottom = band
    if max(band) < 0.01:
        return (
            f"Output size {size} matches the crop aspect. "
            "That crop frame is the output frame. "
            "Do not add a wide empty margin inside it."
        )
    x0, y0 = left, top
    x1, y1 = 1.0 - right, 1.0 - bottom
    return (
        f"Output size is exactly {size}. The primary reference is already padded "
        "to this canvas with solid black bars. "
        f"Picture band: x {x0:.0%}–{x1:.0%}, y {y0:.0%}–{y1:.0%} of the frame. "
        "The black bars are empty padding, not part of the scene. Leave them transparent. "
        "Keep the subject where it sits inside the crop, including the grass or sky "
        "between the subject and the crop edge. "
        "Do not stretch a cap, curl, rim, or bell out to the bars. "
        "If the reference shows empty crop between a tip and the band edge, keep that gap. "
        "Do not move the tip onto the band edge. "
        "Pixels in the black bars are outside the footprint and will be clipped. "
        "Do not draw in the bars. "
        "Do not shrink the subject into a product shot in the middle of the band."
    )


def aspect_pad_rule(canvas_w: int, canvas_h: int, size: str) -> str:
    """Tell the engine how to pad when --size aspect ≠ canvas aspect. Never squash."""
    try:
        ew, eh = [int(x) for x in str(size).lower().split("x")]
    except Exception:
        return (
            f"Target canvas aspect is {canvas_w}:{canvas_h}. "
            "Keep scenic proportions identical to the crop. NEVER squash or stretch."
        )
    target = canvas_w / max(1, canvas_h)
    engine = ew / max(1, eh)
    rel = abs(target - engine) / max(target, engine, 1e-6)
    if rel < 0.08:
        return (
            f"Engine size {size} roughly matches canvas {canvas_w}x{canvas_h} "
            f"(aspect ≈{target:.3f}). Fill the frame with the empty stage — "
            "keep crop proportions; NEVER squash or stretch."
        )
    if engine > target:
        # Engine wider than tall canvas → pillarbox left/right
        return (
            f"Target scene aspect is {canvas_w}:{canvas_h} (≈{target:.3f}); "
            f"engine size {size} is WIDER (≈{engine:.3f}). "
            "Keep the scenic content in the CORRECT taller aspect band centered in the frame; "
            "fill LEFT and RIGHT leftover strips with matching sky/ground continuation "
            "(soft seamless margin OK). NEVER horizontally squash or vertically stretch "
            f"the scene to fill {size}. Compose will cover-crop uniformly — no distortion."
        )
    # Engine taller than wide canvas → letterbox top/bottom
    return (
        f"Target scene aspect is {canvas_w}:{canvas_h} (≈{target:.3f}); "
        f"engine size {size} is TALLER (≈{engine:.3f}). "
        "Keep the scenic content in the CORRECT wider aspect band centered in the frame; "
        "fill TOP and BOTTOM leftover strips with matching sky/ground continuation "
        "(soft seamless margin OK). NEVER squash or stretch the scene to fill "
        f"{size}. Compose will cover-crop uniformly — no distortion."
    )

SHADOW_GROUNDED = (
    "MUST INCLUDE the soft contact/cast shadow under the subject's ground contact "
    "(feet / base / tires / stump / stone ring / log ends) — match the crop's shadow "
    "direction, warmth, and softness. Shadow is part of this layer. "
    "Do NOT omit the shadow. Do NOT paint a full ground-plane carpet of grass/snow."
)
SHADOW_FLYING = (
    "NO ground contact shadow — subject is flying or suspended in air."
)
SHADOW_DISTANT = (
    "Keep a soft light contact shadow under the building base if visible in the crop; "
    "no huge fake oval studio shadow."
)

# 库内回落值；运行时优先读 `.memory-art/config.yaml` → `agent.max_parallel`（见 resolve_default_workers）。
DEFAULT_WORKERS = 4


def resolve_default_workers(start: "Path | None" = None) -> int:
    """Nearest project `agent.max_parallel`, else DEFAULT_WORKERS. Clamped to 1..8."""
    from pathlib import Path

    cur = (start or Path.cwd()).resolve()
    for base in (cur, *cur.parents):
        cfg = base / ".memory-art" / "config.yaml"
        if not cfg.is_file():
            continue
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
            agent = data.get("agent") if isinstance(data, dict) else None
            raw = (agent or {}).get("max_parallel") if isinstance(agent, dict) else None
            if raw is None:
                break
            n = int(raw)
            return max(1, min(8, n))
        except Exception:
            break
    return DEFAULT_WORKERS
