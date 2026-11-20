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
    # bg vs ref NCC inside prop footprints — high ⇒ characters/props still baked into empty stage
    # 0.62 still let soft residue / footprint stains slip on busy camps — tighten for empty-stage quality
    "bg_bake_max": 0.58,
    # bg plate aspect vs canvas after normalize (diagnostic hard fail if still stretched)
    "bg_stretch_err_max": 0.12,
    # autofit scale_mul floor — below this footprint is too loose OR sprite over-zoomed.
    # Catches lantern/heroine ≈0.66 disasters. Occlusion-complete props (rack/woodpile) often
    # land ≈0.78 (complete sprite larger than visible ref patch) — keep floor at 0.75, not 0.82.
    # Fix: tighten plan crop + re-setup (preferred) or re-isolate closer to crop FOV — NEVER widen box.
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
# Size may drift → compose autofit to frozen footprint.
ISOLATE_PROMPT = """STRICT ISOLATE — LOCK LOOK to crop pixels for restore-quality layer split (not a redesign).
Transparent background if the engine supports alpha; otherwise solid pure black isolation plate (no gray, no scene).
References: (1) PRIMARY = generous crop of THIS subject — pixel ground truth for identity/pose/materials.
(2) OPTIONAL SECOND = full scene with THIS subject's box highlighted (outside dimmed) — use only for lighting/style/context continuity; do NOT copy neighbors or the whole scene.
KEEP text only NAMES the slot — do NOT invent details from KEEP alone; match what is visible in the primary crop.
Hard locks (appearance must match the primary crop):
1) SAME camera angle / perspective / FOV as the crop — do NOT change viewpoint
2) SAME composition pose and orientation / silhouette shape as the crop
3) SAME key features, materials, colors, part inventory as visible on the subject in the crop
4) SAME art style as the crop (line, shading, saturation) — extract/split only, do not restyle
5) WHOLE-SUBJECT COMPLETENESS — the full subject must fit inside the output with a clear transparent margin; do NOT clip spear tips, flame tips, hanging charms, cloak hems, limbs, poles, or roof peaks against the image border. Prefer a slightly smaller subject with margin over a cut-off silhouette.
6) NO REDESIGN / NO SPECIES CHANGE — silhouette family must match the crop (A-frame tent stays A-frame, not a draped pavilion; cabin stays the crop viewpoint, not a new frontal house; same spear count / shield layout). A complete but different prop = FAIL.
7) SAME SCENE LIGHTING FAMILY as the crop/context — keep warm fire/lantern bounce AND cool moon/sky rim if both are visible on the subject; do NOT relight into neutral studio softbox or product-shot even lighting on a black void.
Size may be slightly off — compose will autofit to the frozen footprint box; still avoid wild hero-zoom if possible. Prefer subject scale close to the crop (over-zoom forces autofit scale_mul≪1 and breaks restore).
Extract ONLY the listed subject(s). If a neighbor occludes the subject in the crop, complete the hidden part consistently with the crop silhouette — do NOT invent a different object, gender, pose, prop layout, roof type, or species.
If the crop itself cuts the subject (box too tight), still emit a COMPLETE subject matching crop style/geometry — but Agent should have expanded the crop first; do not redesign into a different prop.
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
5) HOLE FILL — where removed objects sat, continue the surrounding grass/snow/floor seamlessly so the empty stage looks naturally unoccupied; no muddy inpaint blobs, no swiss-cheese holes, no scar rings
6) Prop shadows travel WITH prop layers — empty stage must NOT keep those ground shadows
7) Open empty clearing in the middle must remain OPEN — do not refill it with trees/rocks/props to "look pretty"
{aspect_rule}
Sharp clean opaque scenic fill. Empty stage must still match the crop's empty landscape identity when all listed subjects are gone.
"""


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

DEFAULT_WORKERS = 4
