from pathlib import Path
import json
from improve import merge_warm_start_prompt
from skills_kit.must_fix import inject_must_fix
from skills_kit.delivery_gates import generate_prefix

root = Path(__file__).resolve().parents[4]
sess = json.loads((root / ".memory-art/converge/suite_clone.json").read_text(encoding="utf-8"))
base = sess["reasonableness"]["revised_prompt"]
fix = (
    "MUST FIX: stack 4-5 plump spiral cinnamon rolls into a vertical bread tower "
    "with visible spiral layers between rolls; soft-candy glaze toy-cabinet block "
    "highlights near #FEFDFB; reduce photo-real bread pores; keep harbor still life, "
    "no board/HUD/hand."
)
composed = inject_must_fix(base, fix)
merged = merge_warm_start_prompt(composed, sess.get("warm_start") or {})
merged = generate_prefix(sess, merged)
out = Path(__file__).with_name("_final_prompt_r2.txt")
out.write_text(merged, encoding="utf-8")
print("LEN", len(merged))
print(merged[-800:])
