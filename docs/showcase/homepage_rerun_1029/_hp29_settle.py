import json
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
rec = out / "_hp29_record.py"
jobs = json.loads((out / "_hp29_r4.json").read_text(encoding="utf-8"))

history = {
    "clone_kite": [8.53, 8.71, 8.85, 9.03],
    "clone_rabbit": [8.98, 8.93, 9.33, 9.41],
    "variant_light": [9.27, 9.37, 9.21, 9.38],
    "variant_surprise": [8.73, 9.12, 9.31, 9.42],
    "variant_wink": [9.28, 9.41, 9.36, 9.44],
    "variant_sleepy": [9.23, 8.93, 9.36, 9.44],
    "variant_angry": [9.01, 9.32, 9.13, 9.35],
}
dims_hist = {
    "clone_kite": [
        "构图8.2/光影8.6/透视8.4/质感8.8/风格8.9/无瑕疵8.3",
        "构图8.8/光影8.8/透视8.2/质感9.0/风格9.1/无瑕疵8.5",
        "构图9.0/光影8.9/透视8.8/质感9.0/风格8.6/无瑕疵8.8",
    ],
    "clone_rabbit": [
        "构图9.3/光影8.9/透视9.0/质感9.2/风格9.1/无瑕疵8.6",
        "构图9.2/光影9.0/透视8.8/质感9.3/风格8.7/无瑕疵8.7",
        "构图9.4/光影9.2/透视9.3/质感9.4/风格9.5/无瑕疵9.2",
    ],
    "variant_light": [
        "构图9.3/光影9.4/透视9.2/质感9.3/风格9.4/无瑕疵9.1",
        "构图9.4/光影9.5/透视9.3/质感9.4/风格9.5/无瑕疵9.2",
        "构图9.3/光影9.3/透视9.3/质感9.3/风格9.0/无瑕疵9.1",
    ],
    "variant_surprise": [
        "构图9.2/光影9.1/透视9.0/质感9.2/风格7.5/无瑕疵8.4",
        "构图9.3/光影9.2/透视8.8/质感9.3/风格9.3/无瑕疵8.9",
        "构图9.4/光影9.3/透视9.2/质感9.4/风格9.2/无瑕疵9.3",
    ],
    "variant_wink": [
        "构图9.4/光影9.2/透视9.3/质感9.3/风格9.4/无瑕疵9.2",
        "构图9.5/光影9.4/透视9.4/质感9.4/风格9.6/无瑕疵9.3",
        "构图9.4/光影9.3/透视9.3/质感9.4/风格9.5/无瑕疵9.3",
    ],
    "variant_sleepy": [
        "构图9.3/光影9.2/透视9.2/质感9.3/风格9.4/无瑕疵9.1",
        "构图8.8/光影9.2/透视9.2/质感9.3/风格8.4/无瑕疵8.7",
        "构图9.4/光影9.3/透视9.3/质感9.4/风格9.5/无瑕疵9.3",
    ],
    "variant_angry": [
        "构图9.2/光影9.1/透视9.2/质感9.3/风格8.5/无瑕疵8.8",
        "构图9.4/光影9.3/透视9.3/质感9.4/风格9.4/无瑕疵9.2",
        "构图9.3/光影9.2/透视9.3/质感9.4/风格8.7/无瑕疵8.9",
    ],
}

table = []
for j in jobs:
    print("R4 GENERATE", j["session"], flush=True)
    r = subprocess.run(
        [
            sys.executable,
            str(rec),
            "generate",
            "--session",
            j["session"],
            "--round",
            "4",
            "--image",
            j["image"],
            "--prompt",
            j["prompt"],
        ],
        cwd=str(root),
    )
    print(" generate rc", r.returncode, flush=True)
    r = subprocess.run(
        [
            sys.executable,
            str(rec),
            "judge",
            "--session",
            j["session"],
            "--round",
            "4",
            "--image",
            j["image"],
            "--dims",
            j["dims"],
            "--strengths",
            j["strengths"],
            "--defects",
            j["defects"],
            "--next-fix",
            j["next_fix"],
        ],
        cwd=str(root),
    )
    print(" judge rc", r.returncode, flush=True)

    folder = out / j["rel_dir"]
    shutil.copy2(folder / "r4.jpg", folder / "final.jpg")

    scores = history[j["id"]]
    rounds = []
    for i, sc in enumerate(scores, 1):
        rounds.append(
            {
                "round": i,
                "image": f"{j['rel_dir']}/r{i}.jpg",
                "score": sc,
                "dims": dims_hist[j["id"]][i - 1] if i < 4 else j["dims"],
            }
        )
    payload = {
        "id": j["id"],
        "session": j["session"],
        "rounds": 4,
        "scores": scores,
        "best": max(scores),
        "winner": f"{j['rel_dir']}/final.jpg",
        "winner_round": 4,
        "remaining_defect": j["defect"],
        "round_details": rounds,
    }
    (folder / "scores.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (folder / f"{j['id']}_scores.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("FINISH", j["session"], flush=True)
    r = subprocess.run(
        [sys.executable, str(rec), "finish", "--session", j["session"]],
        cwd=str(root),
    )
    print(" finish rc", r.returncode, flush=True)
    table.append(payload)

(out / "v2_clone_variant_results.json").write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
print("DONE", len(table))
