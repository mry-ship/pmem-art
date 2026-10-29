import json
import shutil
from pathlib import Path

REPO = Path(r"C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
OUT = REPO / "docs" / "showcase" / "homepage_rerun_1029"
CELLS = {
    "c02_low": "远鞋体量仍略大，近手仍略简。",
    "c02_medium": "远鞋条纹仍略软，未到 9.6。",
    "c02_high": "手指仍略大，大胆完成度还差一层更密的干粉彩排线。",
    "c02_recompose": "袜筒仍偏长，裁切还没完全停在大腿中段。",
}

summary = []
for cid, defect in CELLS.items():
    scale = cid.split("_", 1)[1]
    sf = REPO / ".memory-art" / "converge" / f"hp29_{cid}.json"
    sess = json.loads(sf.read_text(encoding="utf-8"))
    folder = OUT / "draw_matrix" / "c02" / scale
    rounds = []
    best = None
    for row in sess.get("rounds") or []:
        rno = int(row.get("round") or 0)
        try:
            score = float(row.get("score"))
        except (TypeError, ValueError):
            continue
        rec = {
            "round": rno,
            "image": f"draw_matrix/c02/{scale}/r{rno}.jpg",
            "score": score,
            "dims": row.get("dims_parsed") or row.get("dims") or {},
            "dims_str": row.get("dims") or "",
            "defects": row.get("defects") or "",
            "next_fix": row.get("next_fix") or "",
        }
        rounds.append(rec)
        if best is None or score > best["score"] or (score == best["score"] and rno > best["round"]):
            best = rec
    assert best is not None
    shutil.copy2(folder / f"r{best['round']}.jpg", folder / "final.jpg")
    socks = folder / "socks.jpg"
    if socks.is_file():
        socks.unlink()
    out = {
        "id": cid,
        "session": f"hp29_{cid}",
        "skill": "draw",
        "module": "character.PastelHoodie",
        "scale": scale,
        "family": "dry",
        "threshold": 9.6,
        "max_rounds": 4,
        "n": len(rounds),
        "best": best["score"],
        "winner_round": best["round"],
        "winner": f"draw_matrix/c02/{scale}/final.jpg",
        "remaining_defect": defect,
        "rounds": rounds,
    }
    (folder / "scores.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary.append(
        {
            "id": cid,
            "rounds": len(rounds),
            "scores": [r["score"] for r in rounds],
            "winner": out["winner"],
            "best": out["best"],
            "remaining_defect": defect,
        }
    )
    print(cid, "r" + str(best["round"]), best["score"])

(OUT / "draw_matrix" / "c02" / "c02_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
