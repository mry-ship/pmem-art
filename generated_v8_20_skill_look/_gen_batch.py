"""Generate look-loop jobs: apikey.fan first, else append cursor.GenerateImage pending jobs."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from skills_kit.skill_image_gen import fan_or_generate_image_job  # noqa: E402

jobs = json.loads((ROOT / "generated_v8_20_skill_look" / "_jobs_wave7.json").read_text(encoding="utf-8"))
start, count = int(sys.argv[1]), int(sys.argv[2])
assets = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")
pending_path = ROOT / "generated_v8_20_skill_look" / "pending_gen_jobs.jsonl"

for j in jobs[start : start + count]:
    out = assets / f"{j['bot_id']}_r{j['round']}.jpg"
    pad = Path(j["pad_src"]) if j.get("pad_src") else None
    print("START", j["bot_id"], "R" + str(j["round"]), flush=True)
    res = fan_or_generate_image_job(
        prompt=j["prompt"],
        out_path=out,
        pad_src=pad,
        aspect_ratio=j.get("aspect_ratio") or "1:1",
        bot_id=j["bot_id"],
        round_num=int(j["round"]),
    )
    if res.get("needs_agent_gen"):
        with pending_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"job": j, "agent_job": res.get("agent_job")}, ensure_ascii=False) + "\n")
        print("PENDING GenerateImage", j["bot_id"], res.get("fan_error", "")[:120], flush=True)
    elif res.get("ok"):
        print("OK", out, flush=True)
    else:
        print("FAIL", j["bot_id"], res.get("error"), flush=True)
