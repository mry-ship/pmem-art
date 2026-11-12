from pathlib import Path
import json
from improve import merge_warm_start_prompt
from skills_kit.must_fix import inject_must_fix
from skills_kit.delivery_gates import generate_prefix

root = Path(__file__).resolve().parents[4]
sess = json.loads((root / ".memory-art/converge/suite_clone.json").read_text(encoding="utf-8"))
base = sess["reasonableness"]["revised_prompt"]
fix = (
    "MUST FIX: keep the 5-roll vertical cinnamon tower; rewrite surfaces to soft-candy "
    "glaze toy-cabinet look with chunky #FEFDFB block highlights and no hard outlines; "
    "kill photo-real bread pores and Pixar-hard icing; simplify harbor to soft color-wash "
    "bokeh only (no realistic palms/stone railing)."
)
composed = inject_must_fix(base, fix)
merged = merge_warm_start_prompt(composed, sess.get("warm_start") or {})
merged = generate_prefix(sess, merged)
Path(__file__).with_name("_final_prompt_r3.txt").write_text(merged, encoding="utf-8")
print("LEN", len(merged))
