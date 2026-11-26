"""Converge thresholds and scoring dimension weights. No product imports."""
from __future__ import annotations

DEFAULT_THRESHOLD = 9.5
DEFAULT_MAX_ROUNDS = 3
FAST_SOFT_THRESHOLD = 9.0  # fast-track: prefer fewer regens when score>=9.0 & delta small; final accept still >=9.5 unless draft
# 字节熵只作旁证，不再单独决定图片是否有效。实色探针大约 2.5–2.9，照片通常 ≥6。
MIN_IMAGE_BYTE_ENTROPY = 3.2
MIN_IMAGE_EDGE_PX = 64

UI_DEDICATED_DIM_WEIGHTS: dict[str, float] = {
    "style_palette": 0.25,
    "nine_slice_structure": 0.25,
    "lighting_material": 0.20,
    "rgba_pipeline_compliance": 0.15,
    "state_suite_cohesion": 0.15,
}

APP_ICON_DIM_WEIGHTS: dict[str, float] = {
    "glyph_silhouette": 0.25,
    "squircle_safe_zone": 0.25,
    "tactile_lighting": 0.20,
    "multisize_adaptive": 0.15,
    "palette_purity": 0.15,
}
