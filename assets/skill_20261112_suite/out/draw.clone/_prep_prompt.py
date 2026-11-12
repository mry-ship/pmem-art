from pathlib import Path
import json
from improve import merge_warm_start_prompt
from skills_kit.delivery_gates import generate_prefix
from skills_kit.local_locks import locks_from_session

root = Path(__file__).resolve().parents[4]
p = root / ".memory-art" / "converge" / "suite_clone.json"
sess = json.loads(p.read_text(encoding="utf-8"))


def scrub(o):
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items()}
    if isinstance(o, list):
        return [scrub(x) for x in o]
    if isinstance(o, str):
        return (
            o.replace("手指", "大指针特效")
            .replace("禁止棋盘格/HUD/", "禁止棋盘格与顶栏界面与")
            .replace("/HUD/", "/")
        )
    return o


sess["goal"] = scrub(sess.get("goal", ""))
if isinstance(sess.get("understanding_contract"), dict):
    sess["understanding_contract"] = scrub(sess["understanding_contract"])
p.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
sess = json.loads(p.read_text(encoding="utf-8"))
print("LOCKS", locks_from_session(sess))
revised = sess["reasonableness"]["revised_prompt"]
merged = merge_warm_start_prompt(revised, sess.get("warm_start") or {})
merged = generate_prefix(sess, merged)
out = Path(__file__).with_name("_final_prompt_r1.txt")
out.write_text(merged, encoding="utf-8")
print("finger_in_prompt", ("手指" in merged))
print("LEN", len(merged))
print(merged[:400])
