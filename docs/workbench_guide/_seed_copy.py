#!/usr/bin/env python3
"""Copy + recompress showcase examples into workbench_guide (committed, not gallery-scanned).

Display-oriented JPEGs keep git/page load light while staying clear for artists.
First frame of each lesson is the real 原图 (original), not a process sheet.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path(__file__).resolve().parent
MAX_EDGE = 1280
MAX_EDGE_ALPHA = 768
JPEG_QUALITY = 82

# dest_rel under docs/workbench_guide → source under repo root
COPIES = [
    # 合成梯：第一张必须是海船原图版式，不是过程整表
    ("merge-ladder/original.jpg", "assets/prop/instrumentmerge/ref_boat_5x3_user.jpg"),
    ("merge-ladder/process_r1.jpg", "assets/prop/instrumentmerge/overview_5x3_cursor_refpad.jpg"),
    ("merge-ladder/process_r4.jpg", "assets/prop/instrumentmerge/overview_5x3_cursor_r4.jpg"),
    ("merge-ladder/final.jpg", "assets/prop/instrumentmerge/overview_5x3_rebuild_final.png"),
    # 普通图
    ("draw-ordinary/original.jpg", "assets/skill_battery_20261103/04_prop.png"),
    ("draw-ordinary/process_r1.jpg", "assets/skill_battery_20261103/draw_ordinary_A/r1.png"),
    ("draw-ordinary/final.jpg", "assets/skill_battery_20261103/draw_ordinary_A/r4.png"),
    # 原画
    ("draw-keyart/original.jpg", "assets/skill_battery_20261103/01_style.png"),
    ("draw-keyart/process_r1.jpg", "assets/skill_battery_20261103/draw_keyart/r1.png"),
    ("draw-keyart/final.jpg", "assets/skill_battery_20261103/draw_keyart/r4.png"),
    # 风格克隆（与变体不同：新题材）
    ("draw-clone/original.jpg", "assets/skill_battery_20261103/01_style.png"),
    ("draw-clone/process_r1.jpg", "assets/skill_battery_20261103/rerun_style_lock/r1_916.png"),
    ("draw-clone/final.jpg", "assets/skill_battery_20261103/rerun_style_lock/r4_916.png"),
    # 变体（同一角色差分）
    ("draw-variant/original.jpg", "assets/skill_battery_20261103/02_character.png"),
    ("draw-variant/process_r1.jpg", "assets/skill_battery_20261103/draw_variant/r1.png"),
    ("draw-variant/final.jpg", "assets/skill_battery_20261103/draw_variant/r4.png"),
    # 多图分工
    ("draw-multi/original.jpg", "assets/skill_battery_20261103/03_structure.png"),
    ("draw-multi/process_r1.jpg", "assets/skill_battery_20261103/draw_multi/r1.png"),
    ("draw-multi/process_r2.jpg", "assets/skill_battery_20261103/draw_multi/r2.png"),
    ("draw-multi/final.jpg", "assets/skill_battery_20261103/draw_multi/r4.png"),
    # 图标
    ("icon-a/original.jpg", "assets/skill_battery_20261103/02_character.png"),
    ("icon-a/process_r1.jpg", "assets/skill_battery_20261103/rerun_icon_a/r1.png"),
    ("icon-a/final.jpg", "assets/skill_battery_20261103/rerun_icon_a/r2.png"),
    # 原图保留蘑菇意向（说明「意向≠终稿题材」）；过程/终稿必须是两张不同的爆米花桶
    ("icon-c/original.jpg", "assets/skill_battery_20261103/04_prop.png"),
    ("icon-c/process_r1.png", "assets/skill_battery_20261103/rerun_icon_c/popcorn_r1.png"),
    ("icon-c/final.png", "assets/skill_battery_20261103/rerun_icon_c/popcorn_r2.png"),
    # UI
    ("ui/original.jpg", "assets/skill_battery_20261103/05_ui.png"),
    ("ui/process_r1.jpg", "assets/skill_battery_20261103/rerun_ui/concept_r1.png"),
    ("ui/final.jpg", "assets/skill_battery_20261103/rerun_ui/concept_r2.png"),
    # 锁风格
    ("style-lock/original.jpg", "assets/skill_battery_20261103/01_style.png"),
    ("style-lock/process_r1.jpg", "assets/skill_battery_20261103/style_lock_proof/r1.png"),
    ("style-lock/final.jpg", "assets/skill_battery_20261103/style_lock_proof/r4.png"),
    # 总控 / 提示词 / 只审图：用原图做样例锚点
    ("agent/original.jpg", "assets/prop/instrumentmerge/ref_boat_5x3_user.jpg"),
    ("prompt/original.jpg", "assets/skill_battery_20261103/04_prop.png"),
    ("critique/original.jpg", "assets/skill_battery_20261103/draw_ordinary_A/r4.png"),
]


def _save_display(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = dest.suffix.lower()
    if suffix in {".png"}:
        try:
            from PIL import Image

            im = Image.open(src)
            im = im.convert("RGBA") if im.mode in ("P", "LA") else im.convert("RGBA")
            w, h = im.size
            scale = min(1.0, MAX_EDGE_ALPHA / max(w, h))
            if scale < 1.0:
                im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
            im.save(dest, format="PNG", optimize=True, compress_level=9)
            return
        except Exception:
            shutil.copy2(src, dest)
            return

    try:
        from PIL import Image

        im = Image.open(src)
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (11, 16, 29))
            rgba = im.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, MAX_EDGE / max(w, h))
        if scale < 1.0:
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        im.save(dest, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    except Exception:
        shutil.copy2(src, dest)


def main() -> int:
    manifest = []
    wanted = set()
    for dest_rel, src in COPIES:
        src_p = ROOT / src
        if not src_p.is_file():
            print("MISSING", src)
            continue
        dest = GUIDE / dest_rel
        _save_display(src_p, dest)
        wanted.add(dest.resolve())
        manifest.append(
            {
                "dest": dest_rel.replace("\\", "/"),
                "from": src,
                "bytes": dest.stat().st_size,
            }
        )
        print("OK", dest_rel, dest.stat().st_size)

    for p in GUIDE.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        if p.resolve() not in wanted:
            p.unlink(missing_ok=True)
            print("RM", p.relative_to(GUIDE))

    (GUIDE / "_sources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(x["bytes"] for x in manifest)
    print(f"copied {len(manifest)} · {round(total/1024/1024, 1)} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
