"""pmem-art skills_kit package.

Re-exports public API so `from skills_kit import X` keeps working.
"""
from __future__ import annotations

from lifecycle import ensure_stdio_survives_locale

ensure_stdio_survives_locale()

from ._time import _now_cst

from .skill_specs import SKILL_SPECS
from .install import (
    install_skills_and_agent_configs,
    _render_agent_doc_block,
    _render_command_md,
    _render_skill_md,
    _upsert_markdown_block,
)
from .prompt_scale import (
    APP_ICON_DIM_WEIGHTS,
    CONVERGE_SCALE_PROFILES,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_THRESHOLD,
    FAST_SOFT_THRESHOLD,
    MIN_IMAGE_BYTE_ENTROPY,
    MIN_IMAGE_EDGE_PX,
    AFFIRMATIVE_LOCK_PATTERNS,
    SCALE_BEST_DIRECTION_HINTS,
    UI_DEDICATED_DIM_WEIGHTS,
    _body_without_scale_banner,
    _constraint_tail,
    _infer_case_style_and_subject,
    _prompt_change_ratio,
    _recompose_change_evidence,
    build_best_direction_hint,
    build_dynamic_prompt_directive,
    build_r1_structure_floor,
    check_scale_task_text,
    compose_style_first_prompt,
    find_affirmative_lock_hits,
    get_converge_scale_profile,
    format_dim_weights_zh,
    format_dim_lock_levels_zh,
    format_dim_lock_summary_zh,
    format_lock_override_prompt_hint,
    format_scale_artist_footer,
    parse_dim_lock_overrides,
    merge_dim_lock_overrides,
    resolve_dim_lock_levels,
    SCALE_DIM_LOCK_LEVELS,
    strip_affirmative_locks_from_prompt,
    strip_redline_tags_from_generation_text,
)
from .scoring import (
    _clause_text,
    _is_app_icon_5d_context,
    _is_ui_5d_context,
    _keyword_hits,
    _locally_negated,
    _parse_kv_5d,
    _parse_skill_additive,
    audit_score_inflation,
    defects_are_substantive,
    parse_5d_dims,
)
from .image_gates import (
    CASE_CONFIG_MAP,
    VALID_ASPECT_RATIOS,
    _aspect_relation,
    _infer_canonical_aspect_ratio,
    _inspect_image_physical_traits,
    _parse_ratio_float,
    resolve_case_config,
)
from .validate_params import (
    _physical_image_gate,
    _resolve_round_image_path,
    _round_counts_as_passed,
    _round_has_real_image,
    validate_case_generation_params,
    validate_converge_params,
)
from .judge_auto import auto_vlm_judge_image
from .converge import (
    _session_file,
    cmd_converge,
    converge_finish,
    converge_generate,
    converge_judge,
    converge_start,
    converge_step,
)
