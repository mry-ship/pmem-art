"""c02 PastelHoodie converge helper. Writes only under homepage_rerun_1029 plus session json."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(r"C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
sys.path.insert(0, str(REPO))

OUT = REPO / "docs" / "showcase" / "homepage_rerun_1029"
REF = REPO / "docs" / "showcase" / "homepage_rerun_1028" / "draw_matrix" / "c02" / "ref.jpg"
REF_COPY = OUT / "draw_matrix" / "c02" / "ref.jpg"

from improve.project_library import ensure_project_library_bound  # noqa: E402
import improve as _improve  # noqa: E402
import improve.project_library as _pl  # noqa: E402
import improve.warm_start as _ws  # noqa: E402
import improve.knowledge as _kn  # noqa: E402
import improve.taste_profile as _tp  # noqa: E402
import improve.reflection as _rf  # noqa: E402

_ORIG_BIND = ensure_project_library_bound


def _safe_bind(root, **kwargs):
    meta_path = Path(root) / ".memory-art" / "active_project.json"
    if meta_path.is_file():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return _ORIG_BIND(root, **kwargs)


for _mod in (_pl, _ws, _kn, _tp, _rf, _improve):
    _mod.ensure_project_library_bound = _safe_bind

from pmem_art import load_project  # noqa: E402
from skills_kit.converge import cmd_converge  # noqa: E402
from skills_kit.medium_family import family_weights, weighted_harmonic, GENERAL_6D_KEYS  # noqa: E402

REF_ANALYSIS = (
    "4:3 oil-pastel sitting girl. Camera slight 3/4 from her right-back, body faces right, "
    "head turns looking up-right. Left-weighted hip on ground, closer knee raised, far leg extended, "
    "far sneaker recedes to the right edge (rear/side of shoe). Black bob, red hoodie #E7554D, "
    "blue shorts, BOTH legs over-knee BLACK socks, closer thigh BARE above sock cuff, "
    "white sneakers with three black stripes. Paper #FBF7F0, diagonal blue-grey hatch #647893, "
    "beige hatch upper-right, peach blush, dry crayon tooth, soft flat light, short hip contact shadow. "
    "Do not inherit glued near fingers or far shoe as a crayon smear."
)

LOCK = (
    "4:3 oil-pastel crayon paper. Black bob, red hoodie, blue shorts, BOTH legs over-knee BLACK socks, "
    "near thigh of the closer leg bare above the sock, white sneakers with black stripes. "
    "Diagonal blue-grey crayon background, blush air. No ankle socks, no missing sock, no extra limbs."
)

CELLS = {
    "c02_low": {
        "scale": "low",
        "recompose_dir": "",
        "rel": "draw_matrix/c02/low",
        "goal": (
            f"{LOCK} Scale=low. Only repair one local flaw. Keep camera, pose, identity. "
            "Keep the exact sitting camera: girl in left two-thirds, closer knee raised, "
            "far sneaker receding to the right edge. Only repair: readable separate fingers on the "
            "near hand resting on the raised knee, and a real far white sneaker with sole and three "
            "black stripes instead of a smear. Neighboring pose, socks, hoodie stay locked."
        ),
    },
    "c02_medium": {
        "scale": "medium",
        "recompose_dir": "",
        "rel": "draw_matrix/c02/medium",
        "goal": (
            f"{LOCK} Scale=medium. Small polish, lock camera and socks. "
            "Same sitting pose as the reference. Slightly cleaner dry-pastel hatching on the red hoodie "
            "and sharper black over-knee sock cuffs on BOTH legs. Far sneaker still recedes; "
            "do not open the pose or put both feet side by side facing the camera."
        ),
    },
    "c02_high": {
        "scale": "high",
        "recompose_dir": "",
        "rel": "draw_matrix/c02/high",
        "goal": (
            f"{LOCK} Scale=high. Bolder lighting and finish, keep identity. "
            "Same girl, same sitting silhouette, BOTH over-knee black socks, closer thigh bare. "
            "Bolder layered oil-pastel on the red hoodie, stronger paper tooth and flywhite, "
            "richer diagonal blue-grey hatch, still soft light and short contact shadow. "
            "Do not drop a sock, do not add studio volume light."
        ),
    },
    "c02_recompose": {
        "scale": "recompose",
        "recompose_dir": (
            "Side half-body of the same girl. Old full-figure sitting camera is void. "
            "Crop head to mid-thigh, true side or 3/4 side, seated or still standing. "
            "NOT a full-body walking shot. Over-knee black socks still visible under the crop."
        ),
        "rel": "draw_matrix/c02/recompose",
        "goal": (
            f"{LOCK} Scale=recompose. Same pastel girl, side half-body, still over-knee black socks, "
            "red hoodie, crayon paper. New camera: crop head to mid-thigh. Old sitting full-figure "
            "camera is void. Both over-knee black socks remain visible. Not a walking full body."
        ),
    },
}

DRY_W = family_weights("dry")


def harmonic(dims: dict[str, float]) -> float:
    scores = {
        "composition": dims["composition"],
        "lighting_color": dims["lighting_color"],
        "perspective_anatomy": dims["perspective_anatomy"],
        "texture_detail": dims["texture_detail"],
        "spec_style": dims["spec_style"],
        "flawlessness": dims["flawlessness"],
    }
    return float(weighted_harmonic(scores, DRY_W, GENERAL_6D_KEYS))


def dims_str(dims: dict[str, float]) -> str:
    return (
        f"构图{dims['composition']}/光影{dims['lighting_color']}/"
        f"透视{dims['perspective_anatomy']}/质感{dims['texture_detail']}/"
        f"风格{dims['spec_style']}/无瑕疵{dims['flawlessness']}"
    )


def pmem(action: str, **kwargs) -> int:
    data = load_project(REPO)
    kwargs.setdefault("apply_memory", False)
    return cmd_converge(REPO, data, action, **kwargs)


def start_all() -> None:
    REF_COPY.parent.mkdir(parents=True, exist_ok=True)
    if REF.is_file():
        shutil.copy2(REF, REF_COPY)
    for cid, spec in CELLS.items():
        (OUT / spec["rel"]).mkdir(parents=True, exist_ok=True)
        rc = pmem(
            "start",
            session_id=f"hp29_{cid}",
            goal=spec["goal"],
            module="character.PastelHoodie",
            ref_image=str(REF),
            ref_analysis=REF_ANALYSIS,
            aspect_ratio="4:3",
            reference_image_paths=[str(REF)],
            threshold=9.6,
            max_rounds=4,
            converge_mode="quality",
            scale=spec["scale"],
            recompose_dir=spec["recompose_dir"],
            medium_family="dry",
            silent=False,
        )
        print(f"START hp29_{cid} rc={rc}", flush=True)


def register_round(cid: str, rno: int, image: Path, prompt: str) -> int:
    return pmem(
        "generate",
        session_id=f"hp29_{cid}",
        round_num=rno,
        image=str(image),
        prompt=prompt,
    )


def judge_round(
    cid: str,
    rno: int,
    image: Path,
    dims: dict[str, float],
    strengths: str,
    defects: str,
    next_fix: str,
) -> int:
    return pmem(
        "judge",
        session_id=f"hp29_{cid}",
        round_num=rno,
        image=str(image),
        dims=dims_str(dims),
        strengths=strengths,
        defects=defects,
        next_fix=next_fix,
    )


def finish(cid: str) -> int:
    return pmem("finish", session_id=f"hp29_{cid}", apply_memory=False, silent=True)


def session_score(cid: str, rno: int) -> float | None:
    sf = REPO / ".memory-art" / "converge" / f"hp29_{cid}.json"
    if not sf.is_file():
        return None
    sess = json.loads(sf.read_text(encoding="utf-8"))
    row = next((x for x in sess.get("rounds") or [] if x.get("round") == rno), {})
    try:
        return float(row.get("score"))
    except (TypeError, ValueError):
        return None


def copy_winner(cid: str, src: Path) -> Path:
    dest = OUT / CELLS[cid]["rel"] / "final.jpg"
    shutil.copy2(src, dest)
    return dest


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        start_all()
    elif cmd == "score":
        dims = json.loads(sys.argv[2])
        print(harmonic(dims))
    else:
        raise SystemExit(f"unknown {cmd}")
