#!/usr/bin/env python3
"""
Tests for pmem-art Two-Layer Memory Architecture:
1. Project-Private Layer (.memory-art/) strict isolation across projects (modules, redlines, taste, recipes, style-bound cards).
2. Cross-Project Shared Layer (~/.pmem-art/shared/ or PMEM_ART_SHARED_DIR) holding only style-agnostic universal knowledge cards.
3. New empty project cold-start auto-loads Shared Layer into Warm-Start while Private Layer starts empty.
4. Promotion from Private Layer to Shared Layer allows universal rules and blocks style-specific/HEX-bound cards.
5. `rank_memory_entry` ranks Project-Private entries/cards strictly higher than Shared-Layer entries/cards when both match.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from improve import (
    build_warm_start_pack,
    ensure_shared_knowledge_seeded,
    is_style_agnostic_universal_card,
    load_knowledge_index,
    load_shared_knowledge_index,
    promote_card_to_shared,
    rank_memory_entry,
    recall_layered_knowledge_cards,
    upsert_knowledge_card,
)
from pmem_art import load_project
from build_atlas import generate_atlas_html


def run_cli(proj_dir: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "pmem_art.py"), "--root", str(proj_dir), *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )


def main() -> None:
    tmp_base = Path("/tmp/pmem_two_layer_test")
    if tmp_base.exists():
        shutil.rmtree(tmp_base)
    tmp_base.mkdir(parents=True)

    shared_dir = tmp_base / "global_shared"
    proj_a = tmp_base / "ProjectA_Celadon"
    proj_b = tmp_base / "ProjectB_Cyberpunk"

    env = dict(os.environ)
    env["PMEM_ART_SHARED_DIR"] = str(shared_dir)
    os.environ["PMEM_ART_SHARED_DIR"] = str(shared_dir)

    # 1. Initialize Project A and verify Private Layer is empty while Shared Layer is seeded
    run_cli(proj_a, "init", "--name", "Project A (东方青瓷)", env=env)
    priv_idx_a = load_knowledge_index(proj_a)
    shared_idx = load_shared_knowledge_index(proj_a, auto_seed=True)
    assert len(priv_idx_a.get("cards") or {}) == 0, "New project private knowledge layer must start empty"
    assert len(shared_idx.get("cards") or {}) >= 8, "Global shared layer must be auto-seeded with universal cards"

    # 2. Add project-specific memories & style cards to Project A, plus a new universal craft card
    run_cli(
        proj_a,
        "feedback",
        "这版阿斯特拉青瓷白#84A98C配玄青#1C2541留着当正例；严禁赛博霓虹紫#FF00FF",
        "-m",
        "character.Hero",
        env=env,
    )
    # Style-bound card in Project A (should NOT promote to shared layer)
    upsert_knowledge_card(
        proj_a,
        card_id="style-celadon-lock",
        title="青瓷水彩专属色板锁",
        body="主色锁定青瓷#84A98C与玄青#1C2541，严禁赛博霓虹紫",
        tags=["character", "style_lock"],
        source="project_a",
        promote_if_universal=True,
    )
    # Universal style-agnostic card discovered in Project A (SHOULD auto-promote to shared layer)
    upsert_knowledge_card(
        proj_a,
        card_id="universal-hand-foreshortening",
        title="手部透视缩短三段法",
        body="手掌朝向镜头时，先画掌根方盒截面，再按近大远小叠指节圆柱，严禁平铺五指。",
        tags=["anatomy", "character"],
        source="project_a",
        promote_if_universal=True,
    )

    shared_after_a = load_shared_knowledge_index(proj_a, auto_seed=False).get("cards") or {}
    assert "universal-hand-foreshortening" in shared_after_a, "Universal card should be promoted to shared layer"
    assert "style-celadon-lock" not in shared_after_a, "Style/HEX-bound card must NEVER leak to shared layer"

    # Explicit promote call on style-bound card must be blocked by purity guard
    prom_blocked = promote_card_to_shared(proj_a, "style-celadon-lock", force=False)
    assert not prom_blocked["ok"], "Guard must block style-bound card promotion"

    # 3. Initialize brand-new Project B and verify strict Private Layer isolation + Shared Layer warm-start
    run_cli(proj_b, "init", "--name", "Project B (全新废土机甲项目)", env=env)
    data_b = load_project(proj_b)
    assert len(data_b["entries"]) == 0, "Project B private entries must be 0 (no leak from Project A)"
    assert not data_b["profile"]["taste"].get("banned_habits"), "Project B private taste must be empty (no leak from Project A)"
    assert len(data_b["profile"]["private_knowledge_cards"]) == 0, "Project B private knowledge cards must be 0"

    warm_b = build_warm_start_pack(proj_b, data_b, module="character.Hero", goal="机甲驾驶员全身立绘 手部透视 头身比")
    shared_ids_in_warm_b = {c["id"] for c in warm_b.get("shared_knowledge") or []}
    assert "universal-hand-foreshortening" in shared_ids_in_warm_b or "anatomy-head-ratio" in shared_ids_in_warm_b, (
        "New project B warm-start must auto-load universal shared knowledge cards"
    )
    assert "style-celadon-lock" not in shared_ids_in_warm_b, "Project A style card must not appear in Project B"
    assert "青瓷" not in warm_b["prompt_block"], "Project A specific colors/styles must not leak into Project B prompt_block"

    # 4. Verify `rank_memory_entry` ranks Project-Private higher than Cross-Project Shared when both match
    shared_entry = {
        "id": "SH01",
        "layer_scope": "shared",
        "module": "character.Hero",
        "tags": ["character", "anatomy"],
        "summary": "通用头身比尺规 7.5头身",
        "body": "立绘常用 7.5 头身刻度",
        "score": 9.8,
        "verified": "2026-10-25",
    }
    private_entry = {
        "id": "PR01",
        "layer_scope": "private",
        "module": "character.Hero",
        "tags": ["character", "anatomy"],
        "summary": "本项目主角头身比尺规 7.5头身",
        "body": "本项目主角锁定 7.5 头身刻度",
        "score": 9.0,
        "verified": "2026-10-24",
    }
    k_priv = rank_memory_entry(private_entry, target_module="character.Hero", query="7.5头身")
    k_shar = rank_memory_entry(shared_entry, target_module="character.Hero", query="7.5头身")
    assert k_priv > k_shar, f"Project-private entry {k_priv} must rank strictly above shared entry {k_shar}"

    # Verify layered knowledge recall in Project A ranks Project A's private cards above shared cards
    recalled_a = recall_layered_knowledge_cards(proj_a, target_module="character.Hero", query="手部透视 头身比", limit=6)
    assert recalled_a[0]["layer_scope"] == "private", "Private layer cards must sort before shared layer cards"

    # 5. Verify Atlas generation includes both layers cleanly
    atlas_out = generate_atlas_html(load_project(proj_a), proj_a / "art-atlas.html")
    atlas_html = atlas_out.read_text(encoding="utf-8")
    assert "跨项目共享层 (Shared)" in atlas_html and "项目私有层 (Private)" in atlas_html

    print("ALL TWO-LAYER MEMORY TESTS PASSED!")


if __name__ == "__main__":
    main()
