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
    # whole-compose ghost QA
    "ghost_mae_warn": 28.0,
    "ghost_mae_fail": 48.0,
    # per-id retry budget
    "max_retries": 2,
}

# {shadow_rule} filled from layer.grounded (see isolate.shadow_rule_for)
ISOLATE_PROMPT = """STRICT ISOLATE. Transparent background.
Crop is REFERENCE only — extract ONLY listed subject(s). Do NOT copy the whole tile.
Center with modest padding. Complete occluded parts of the subject.
Natural proportions — do NOT squash.
{shadow_rule}
No large fake oval drop-shadow. No dirt/snow/grass ground plane fill.
KEEP ONLY: {keep}
MUST REMOVE: {remove}, neighbors, ground fill, sky.
Match crop art style. No redesign.
"""

# Background must be a sharp empty-stage plate (default path = image2.5, not local dig).
BG_ISOLATE_PROMPT = """EMPTY STAGE BACKGROUND plate for layer stacking.
Use the reference full scene for layout/colors/style ONLY.
KEEP ONLY: {keep}
MUST REMOVE: {remove}, every character, every prop, houses/boats/lamps if listed — do NOT bake them into the background.
Full-bleed scenic background, sharp and clean (not muddy, not smeared inpaint).
Opaque scenic fill preferred (no swiss-cheese holes). Match crop art style. No redesign of camera or composition.
"""

SHADOW_GROUNDED = (
    "Keep a tiny soft contact shadow only under the subject's ground contact "
    "(feet/base/tires/stump). Do not paint a full ground plane."
)
SHADOW_FLYING = (
    "NO ground contact shadow — subject is flying or suspended in air."
)
SHADOW_DISTANT = (
    "Skip ground contact shadow for distant architecture; no fake oval shadow."
)

DEFAULT_WORKERS = 4
