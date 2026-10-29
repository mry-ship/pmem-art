"""c01 NightCity converge helper. Writes only under homepage_rerun_1029 plus session json."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from PIL import Image

REPO = Path(r"C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
sys.path.insert(0, str(REPO))

OUT = REPO / "docs" / "showcase" / "homepage_rerun_1029"
REF = REPO / "docs" / "showcase" / "homepage_rerun_1028" / "draw_matrix" / "c01" / "ref.jpg"
REF_COPY = OUT / "draw_matrix" / "c01" / "ref.jpg"
ASSETS = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")

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

LOCK = (
    "PIXEL LOCK: 9:16 epic night. Pale-robe dark-hair swordsman standing on CHARCOAL WET dark roof tiles "
    "(NOT green glaze). Warm WINDOW FIRE lights in the vast city below, cool fog, planetary limb. "
    "No lantern as key light. No starfield replacing the city. No neon."
)

REF_ANALYSIS = (
    "9:16 epic night cinematic still. Extreme high three-quarter looking down a central avenue that "
    "vanishes into a curved planetary city limb. Pale-robe dark-hair swordsman back-view on the lower-left "
    "roof ridge, near-silhouette, sheathed sword at left hip. CHARCOAL WET overlapping clay tiles, soot-black, "
    "faint dirty frost on ridges — not green glaze. Warm WINDOW FIRE as small amber rectangles in windows; "
    "cool blue-grey fog in streets. Palette: charcoal tiles #1A1C1E, pale robe #C9C4BB, cool fog #6B7480, "
    "window fire #E8A040, night #243038. Window-fires are the only warm sources. Do not inherit lanterns, "
    "neon, starfields, or green tiles."
)

PHOTO_W = family_weights("photo")

CELLS = {
    "c01_low": {
        "scale": "low",
        "recompose_dir": "",
        "rel": "draw_matrix/c01/low",
        "winner_round": 3,
        "remaining_defect": "Near tiles still a little frost-sparkly versus the reference dirtier wet charcoal.",
        "goal": (
            f"{LOCK} Scale=low. Only repair one local lighting flaw; keep camera and identity. "
            "Add a faint warm window-fire bounce specular on the nearest charcoal wet tile ridges. "
            "Do not lantern-light the warrior. Camera locked: high three-quarter, warrior lower-left on the ridge."
        ),
    },
    "c01_medium": {
        "scale": "medium",
        "recompose_dir": "",
        "rel": "draw_matrix/c01/medium",
        "winner_round": 4,
        "remaining_defect": "Near tiles still a little snow-sparkle; city lights a bit pointier than the reference softer window-fire clusters.",
        "goal": (
            f"{LOCK} Scale=medium. Small polish, lock camera. Crisper wet charcoal tile grain and cleaner "
            "cool-fog versus window-fire separation. Same pose, costume, and city layout."
        ),
    },
    "c01_high": {
        "scale": "high",
        "recompose_dir": "",
        "rel": "draw_matrix/c01/high",
        "winner_round": 4,
        "remaining_defect": "Central avenue still slightly bloomed versus fully discrete window-fire points.",
        "goal": (
            f"{LOCK} Scale=high. Bolder lighting finish, keep identity. Stronger cool fog against hotter "
            "window-fire clusters; wet charcoal tiles catch amber bounce. No lanterns, no green tiles."
        ),
    },
    "c01_recompose": {
        "scale": "recompose",
        "recompose_dir": (
            "Stand in the central long street looking UP at ridges; warrior becomes a small silhouette "
            "on a ridge; fog separates street from window-fire sea. Old high-roof looking-down camera is void."
        ),
        "rel": "draw_matrix/c01/recompose",
        "winner_round": 3,
        "remaining_defect": "Camera never left the high-roof looking-down shot; warrior remains a large foreground figure.",
        "goal": (
            f"{LOCK} Scale=recompose. Camera in the central long street looking UP at ridges; warrior a small "
            "silhouette on a ridge; fog separates street from window-fire sea. Keep charcoal tiles and window fire. "
            "Old high-roof looking-down camera is void."
        ),
    },
}

ROUNDS = {
    "c01_low": [
        {
            "prompt": (
                "Cinematic 9:16 epic night still matching the reference camera exactly. Pale-grey-robe dark-hair "
                "xianxia swordsman back-view on CHARCOAL WET dark grey-black traditional roof tiles. LOCAL LIGHTING "
                "FIX ONLY: faint warm window-fire bounce on nearest charcoal wet tile ridges. No lantern key."
            ),
            "dims": {"构图": 8.8, "光影": 7.9, "透视": 8.6, "质感": 8.2, "风格": 8.5, "无瑕疵": 8.3},
            "strengths": "Camera locked; charcoal tiles not green; warrior present; planetary limb and cool fog hold.",
            "defects": "Warrior robe is too bright white versus the reference near-silhouette; tiles read a bit like wet wood.",
            "next_fix": "Dim the swordsman back to a near-silhouette; keep only faint amber bounce on nearest tile ridges.",
        },
        {
            "prompt": (
                "Same locked camera. Dim the swordsman to a near-silhouette like the reference. Pale robe reads dark grey "
                "in city backlight, not bright white. Faint amber bounce on nearest charcoal wet tile ridges. No lantern."
            ),
            "dims": {"构图": 9.2, "光影": 9.0, "透视": 9.0, "质感": 8.7, "风格": 9.1, "无瑕疵": 8.8},
            "strengths": "Silhouette restored; cool fog and discrete window fires; camera still locked; no lanterns.",
            "defects": "Foreground tiles still a bit wood-plank rather than overlapping charcoal clay scales.",
            "next_fix": "Replace wood-plank reading with overlapping charcoal clay tiles; keep the warrior a dark silhouette.",
        },
        {
            "prompt": (
                "Same locked camera. Overlapping charcoal wet clay roof TILES, soot-black, not wood planks, not green glaze. "
                "Warrior remains a dark silhouette. Cool fog and small amber window fires."
            ),
            "dims": {"构图": 9.3, "光影": 9.1, "透视": 9.1, "质感": 9.0, "风格": 9.2, "无瑕疵": 8.9},
            "strengths": "Clay-scale tiles, locked camera, silhouette, cool fog, window fires, planetary limb.",
            "defects": "Tile ridges still a little frost-sparkly versus the reference dirtier wet charcoal.",
            "next_fix": "Reduce sparkly frost so tiles read as wet dirty charcoal clay; keep the warrior a dark silhouette.",
        },
        {
            "prompt": (
                "Same locked camera. Dirtier wet charcoal clay tiles with less sparkly frost. Warrior stays a near-silhouette. "
                "Cool fog, small amber window fires, planetary limb. No lantern."
            ),
            "dims": {"构图": 9.1, "光影": 8.4, "透视": 9.0, "质感": 8.5, "风格": 9.0, "无瑕疵": 8.5},
            "strengths": "Camera and identity still hold; tiles remain charcoal not green.",
            "defects": "Regression: warrior brightened again and frost sparkle increased versus r3.",
            "next_fix": "Stop. Best-of-4 is r3.",
        },
    ],
    "c01_medium": [
        {
            "prompt": (
                "Cinematic 9:16 epic night, camera locked to the reference. Small polish: crisper wet charcoal tile grain "
                "and cleaner cool-fog versus window-fire separation. No lantern, no green tiles."
            ),
            "dims": {"构图": 8.4, "光影": 7.2, "透视": 8.5, "质感": 7.6, "风格": 8.0, "无瑕疵": 7.8},
            "strengths": "Camera and warrior identity roughly hold; planetary limb present.",
            "defects": "Wrong lighting: warm orange haze washes the city; cool fog lost; tiles too brown-wood.",
            "next_fix": "Restore cool blue-grey fog; keep window fires as small discrete amber rectangles, not a warm wash.",
        },
        {
            "prompt": (
                "Same locked camera. Restore cool blue-grey fog. Window lights as small discrete amber rectangles, not orange haze. "
                "Charcoal wet dark tiles, not brown wood."
            ),
            "dims": {"构图": 9.1, "光影": 8.9, "透视": 9.0, "质感": 8.7, "风格": 9.0, "无瑕疵": 8.8},
            "strengths": "Cool fog restored; discrete window fires; charcoal tiles; silhouette; camera locked.",
            "defects": "Central avenue window-fires a tad dim versus the reference warmer clustered windows.",
            "next_fix": "Slightly denser warmer discrete window-fire points along the central avenue only; keep cool fog on the sides.",
        },
        {
            "prompt": (
                "Same locked camera. Denser discrete amber window-fire points along the central avenue; surrounding city stays cool fog. "
                "Charcoal wet clay tiles. Warrior near-silhouette."
            ),
            "dims": {"构图": 9.2, "光影": 9.0, "透视": 9.1, "质感": 8.9, "风格": 9.1, "无瑕疵": 8.9},
            "strengths": "Avenue fires denser; cool sides; clay tiles; locked camera; no lanterns.",
            "defects": "Nearest tile ridges still lack a faint wet specular from the city below.",
            "next_fix": "Add a faint wet specular bounce on the nearest charcoal tile ridges from the window-fires, without brightening the warrior.",
        },
        {
            "prompt": (
                "Same locked camera. Faint wet specular bounce on nearest charcoal tile ridges from city window-fires. "
                "Cool fog, denser discrete avenue fires, warrior near-silhouette. No lantern."
            ),
            "dims": {"构图": 9.3, "光影": 9.2, "透视": 9.1, "质感": 9.1, "风格": 9.2, "无瑕疵": 9.0},
            "strengths": "Wet charcoal bounce, cool fog, discrete fires, locked camera, identity held.",
            "defects": "Near tiles still a little snow-sparkle versus the reference dirtier wet charcoal.",
            "next_fix": "Stop. Best-of-4 is r4.",
        },
    ],
    "c01_high": [
        {
            "prompt": (
                "Same identity. Bolder lighting finish: stronger cool fog against hotter clustered window fires; wet charcoal "
                "tiles catch amber bounce. No lantern as key light."
            ),
            "dims": {"构图": 8.5, "光影": 6.8, "透视": 8.4, "质感": 8.0, "风格": 7.6, "无瑕疵": 7.4},
            "strengths": "Warrior identity and charcoal tiles hold; planetary limb present.",
            "defects": "Wrong lighting: city became molten fire-glow / lantern-like bloom; cool fog lost.",
            "next_fix": "Keep bolder contrast but restore cool fog; window fires as dense discrete amber points, not molten bloom.",
        },
        {
            "prompt": (
                "Same identity. Bolder contrast with restored cool blue-grey fog. Dense discrete amber window-fire points, "
                "not molten bloom, not lantern glow on the warrior. Wet charcoal bounce."
            ),
            "dims": {"构图": 9.0, "光影": 8.8, "透视": 8.9, "质感": 8.6, "风格": 8.9, "无瑕疵": 8.6},
            "strengths": "Cool fog back; discrete fires; charcoal tiles; identity; no lanterns.",
            "defects": "Planetary limb washed with a little warm haze; tiles still slightly woody.",
            "next_fix": "Cool the planetary limb and sky back to dim blue-grey night; keep window fires as points not bloom.",
        },
        {
            "prompt": (
                "Same identity. Dense discrete amber window fires on the avenue, cool fog on the sides, dim blue-grey planetary limb. "
                "No center molten wash. Charcoal wet clay tiles."
            ),
            "dims": {"构图": 9.1, "光影": 8.7, "透视": 9.0, "质感": 8.8, "风格": 8.9, "无瑕疵": 8.6},
            "strengths": "Cooler limb; identity held; charcoal tiles; bolder avenue.",
            "defects": "City center still bloomed versus sharp small window-fire points.",
            "next_fix": "Reduce center bloom; keep window fires as sharp small points with higher contrast against cool fog.",
        },
        {
            "prompt": (
                "Same identity. Reduce center bloom. Sharp small window-fire points, cool fog on the sides, dim blue-grey planetary limb. "
                "Wet charcoal tiles catch a little amber bounce. No lantern."
            ),
            "dims": {"构图": 9.2, "光影": 8.9, "透视": 9.1, "质感": 9.0, "风格": 9.0, "无瑕疵": 8.8},
            "strengths": "Bolder avenue versus cool sides; charcoal wet tiles; identity; no lanterns.",
            "defects": "Central avenue still slightly bloomed versus fully discrete window-fire points.",
            "next_fix": "Stop. Best-of-4 is r4.",
        },
    ],
    "c01_recompose": [
        {
            "prompt": (
                "NEW CAMERA. Stand IN the central long street looking UP at ridges. Warrior becomes a SMALL silhouette on a distant "
                "ridge. Fog separates street from window-fire sea. Charcoal wet tiles. Old looking-down roof shot is void."
            ),
            "dims": {"构图": 5.2, "光影": 8.0, "透视": 8.0, "质感": 8.2, "风格": 8.2, "无瑕疵": 6.5},
            "strengths": "Charcoal tiles, cool fog, window fires, warrior still present.",
            "defects": "Did not recompose: still high-roof looking down; warrior still a large foreground figure.",
            "next_fix": "Move camera into the street looking UP; make the warrior a tiny ridge silhouette, not a large foreground person.",
        },
        {
            "prompt": (
                "NEW CAMERA. Street-level looking UP. Lower third charcoal wet eaves. Warrior is a SMALL distant silhouette on a ridge. "
                "Fog fills the street canyon. Do not keep the high-roof looking-down shot."
            ),
            "dims": {"构图": 5.0, "光影": 8.2, "透视": 8.0, "质感": 8.3, "风格": 8.3, "无瑕疵": 6.4},
            "strengths": "Materials still charcoal and cool-fog; no green tiles.",
            "defects": "Camera still the old high-roof looking-down shot; warrior still large in the foreground.",
            "next_fix": "Force worm's-eye street camera looking UP; warrior only 5 percent of frame height on a distant ridge.",
        },
        {
            "prompt": (
                "LOW-ANGLE street-level looking UP. Large foreground swordsman from the reference is gone. Tiny dark silhouette on a "
                "distant ridge. Charcoal wet eaves close to lens. Fog separates street from window-fire sea."
            ),
            "dims": {"构图": 5.0, "光影": 8.3, "透视": 8.1, "质感": 8.5, "风格": 8.4, "无瑕疵": 6.5},
            "strengths": "Better clay-tile material and cool fog; window fires stay window-fires.",
            "defects": "Camera still looking down from a roof; warrior still large. Recompose failed.",
            "next_fix": "Last attempt: cobblestone worm's-eye looking straight up the avenue; no large near-roof person.",
        },
        {
            "prompt": (
                "Worm's-eye from cobblestones looking straight UP a long night avenue. Towering charcoal wet eaves left and right. "
                "Warrior only a SMALL silhouette on one high ridge. Do not place a large person on a near roof."
            ),
            "dims": {"构图": 5.0, "光影": 8.0, "透视": 8.0, "质感": 8.2, "风格": 8.2, "无瑕疵": 6.4},
            "strengths": "Tiles remain charcoal; lights remain window fires.",
            "defects": "Still the original high-roof camera; warrior still a large foreground figure. Four-round recompose miss.",
            "next_fix": "Stop. Best-of-4 is r3 for material quality despite the failed camera change.",
        },
    ],
}


def harmonic(dims_zh: dict[str, float]) -> float:
    mapping = {
        "构图": "composition",
        "光影": "lighting_color",
        "透视": "perspective_anatomy",
        "质感": "texture_detail",
        "风格": "spec_style",
        "无瑕疵": "flawlessness",
    }
    scores = {mapping[k]: v for k, v in dims_zh.items()}
    return float(weighted_harmonic(scores, PHOTO_W, GENERAL_6D_KEYS))


def dims_str(dims_zh: dict[str, float]) -> str:
    return (
        f"构图{dims_zh['构图']}/光影{dims_zh['光影']}/透视{dims_zh['透视']}/"
        f"质感{dims_zh['质感']}/风格{dims_zh['风格']}/无瑕疵{dims_zh['无瑕疵']}"
    )


def pmem(action: str, **kwargs) -> int:
    data = load_project(REPO)
    kwargs.setdefault("apply_memory", False)
    return cmd_converge(REPO, data, action, **kwargs)


def jpg_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img.save(dst, "JPEG", quality=95)


def ingest_r4() -> None:
    for cid in CELLS:
        src = ASSETS / f"{cid}_r4.jpg"
        dst = OUT / CELLS[cid]["rel"] / "r4.jpg"
        if src.is_file():
            jpg_copy(src, dst)
            print(f"copied {src.name} -> {dst}", flush=True)
        else:
            print(f"MISSING {src}", flush=True)


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
            module="scene.NightCity",
            ref_image=str(REF),
            ref_analysis=REF_ANALYSIS,
            aspect_ratio="9:16",
            reference_image_paths=[str(REF)],
            threshold=9.6,
            max_rounds=4,
            converge_mode="quality",
            scale=spec["scale"],
            recompose_dir=spec["recompose_dir"],
            medium_family="摄影",
            silent=False,
        )
        print(f"START hp29_{cid} rc={rc}", flush=True)


def apply_all() -> None:
    ingest_r4()
    start_all()
    table = []
    for cid, spec in CELLS.items():
        cell = OUT / spec["rel"]
        rows = []
        for i, rnd in enumerate(ROUNDS[cid], start=1):
            image = cell / f"r{i}.jpg"
            rc_g = pmem(
                "generate",
                session_id=f"hp29_{cid}",
                round_num=i,
                image=str(image),
                prompt=rnd["prompt"],
            )
            rc_j = pmem(
                "judge",
                session_id=f"hp29_{cid}",
                round_num=i,
                image=str(image),
                dims=dims_str(rnd["dims"]),
                strengths=rnd["strengths"],
                defects=rnd["defects"],
                next_fix=rnd["next_fix"],
            )
            total = round(harmonic(rnd["dims"]), 2)
            print(f"JUDGE hp29_{cid} r{i} local={total} generate={rc_g} judge={rc_j}", flush=True)
            rows.append(
                {
                    "round": i,
                    "image": f"r{i}.jpg",
                    "dims": rnd["dims"],
                    "total": total,
                    "strengths": rnd["strengths"],
                    "defects": rnd["defects"],
                    "next_fix": rnd["next_fix"],
                }
            )
        wr = int(spec["winner_round"])
        winner_src = cell / f"r{wr}.jpg"
        winner_dst = cell / "final.jpg"
        shutil.copy2(winner_src, winner_dst)
        rc_f = pmem("finish", session_id=f"hp29_{cid}", apply_memory=False, silent=True)
        print(f"FINISH hp29_{cid} rc={rc_f} winner=r{wr}", flush=True)
        payload = {
            "id": cid,
            "scale": spec["scale"],
            "module": "scene.NightCity",
            "session": f"hp29_{cid}",
            "threshold": 9.6,
            "medium_family": "photo",
            "rounds": 4,
            "scores": rows,
            "winner_round": wr,
            "winner_score": rows[wr - 1]["total"],
            "winner_path": str(winner_dst.relative_to(REPO)).replace("\\", "/"),
            "remaining_defect": spec["remaining_defect"],
        }
        (cell / "scores.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        table.append(payload)
    summary = OUT / "draw_matrix" / "c01" / "summary.json"
    summary.write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", summary, flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "apply"
    if cmd == "apply":
        apply_all()
    elif cmd == "start":
        start_all()
    else:
        raise SystemExit(f"unknown {cmd}")
