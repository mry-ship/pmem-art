# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
draft = "一组饮料合成梯整表，热可可8档，未写链型。"
revised = (root / "assets/skill_20261111_drink/merge_cocoa/prompt_r1.txt").read_text(
    encoding="utf-8"
)
checklist = (
    "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;"
    "single_centered_item=ok;chain_mode_declared=ok;upgrade_reason_concrete=ok;"
    "family_or_base_lock=ok;sheet_safe_zone=ok"
)
cmd = [
    "py",
    "-3",
    "-u",
    "pmem_art.py",
    "reasonableness",
    "review",
    "--id",
    "merge_cocoa_20261111",
    "--skill",
    "merge",
    "--draft",
    draft,
    "--revised",
    revised,
    "--checklist",
    checklist,
]
out = root / "assets/skill_20261111_drink/merge_cocoa/reason_out2.txt"
with out.open("w", encoding="utf-8") as f:
    r = subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT, text=True)
print("EXIT", r.returncode)
sys.exit(r.returncode)
