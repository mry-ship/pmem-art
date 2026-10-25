"""pmem-art improve package — continuous self-iteration.

Public API is re-exported here so `from improve import X` keeps working.
"""
from __future__ import annotations

from ._time import _now_cst

from .project_library import (
    ACTIVE_PROJECT_FILE,
    DEFAULT_TASTE,
    PROFILE_DIR,
    PROJECTS_DIR,
    REFLECTIONS_DIR,
    TASTE_FILE,
    active_project_meta_path,
    ensure_project_library_bound,
    project_library_dir,
    projects_root_dir,
    slugify_project_id,
    sync_active_project_to_library,
)
from .taste_profile import (
    BAN_HINTS,
    COMPOSITION_HINTS,
    LIGHTING_HINTS,
    LINE_HINTS,
    TEMP_HINTS,
    _extract_hints,
    _mem_root,
    _uniq_append,
    apply_feedback_to_taste,
    load_taste,
    profile_dir,
    reflections_dir,
    save_taste,
    taste_path,
)
from .warm_start import (
    build_warm_start_pack,
    extract_entry_score,
    print_warm_start,
    rank_memory_entry,
)
from .reflection import list_reflections, write_session_reflection
from .lessons import (
    DRILLS,
    WEAKNESS_CATEGORIES,
    _drop_dim_label_clauses,
    _is_dim_label_only,
    classify_weakness,
    craft_lessons_from_round,
    print_round_lessons,
)
from .improve_cmds import cmd_improve, cmd_progress, cmd_taste, run_improve_pass
from .autopilot import (
    CATEGORY_TIP_ZH,
    TIP_BUDGET_FILE,
    build_coach_plan,
    cmd_coach,
    compose_whisper_tip,
    print_whisper_tip,
    run_silent_autopilot,
    tip_budget_path,
    try_consume_tip_budget,
)
from .knowledge import (
    ADJACENT_BREADTH,
    DOMAIN_SEED_CARDS,
    KNOWLEDGE_DIR,
    STYLE_SPECIFIC_PATTERNS,
    accept_breadth_proposals,
    cmd_learn,
    ensure_shared_knowledge_seeded,
    has_hand_or_foot_defect,
    ingest_term_to_knowledge,
    is_style_agnostic_universal_card,
    knowledge_dir,
    load_knowledge_index,
    load_shared_knowledge_index,
    promote_card_to_shared,
    propose_breadth_expansions,
    recall_layered_knowledge_cards,
    save_knowledge_index,
    save_shared_knowledge_index,
    shared_knowledge_dir,
    upsert_knowledge_card,
    upsert_shared_knowledge_card,
)
