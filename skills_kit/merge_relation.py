"""art-merge 第一段关系稿校验 + 阶梯方图体量审计 + 整梯等分切格。"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore


@dataclass
class LadderRow:
    level: int
    name: str
    silhouette: str
    scale_delta: str
    scale_pct: float
    parts_add: str


def load_phase1(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "tracks" not in data:
        raise ValueError("phase1 文件需包含 tracks: { id: { rows: [...] } }")
    return data


def parse_rows(track: dict[str, Any]) -> list[LadderRow]:
    rows_raw = track.get("rows") or []
    if len(rows_raw) != 8:
        raise ValueError(f"必须正好 8 行，当前 {len(rows_raw)}")
    out: list[LadderRow] = []
    for r in rows_raw:
        out.append(
            LadderRow(
                level=int(r["level"]),
                name=str(r["name"]).strip(),
                silhouette=str(r["silhouette"]).strip(),
                scale_delta=str(r.get("scale_delta", "")).strip(),
                scale_pct=float(r["scale_pct"]),
                parts_add=str(r.get("parts_add", "")).strip(),
            )
        )
    out.sort(key=lambda x: x.level)
    if [x.level for x in out] != list(range(1, 9)):
        raise ValueError("level 必须为 1..8 连续")
    return out


_EMPTY_PARTS = {"", "—", "-", "－", "无", "没有", "同上", "无新增", "none"}
_WEAK_PARTS = {
    "更华丽",
    "华丽",
    "加光",
    "光效",
    "特效",
    "加特效",
    "fx",
    "glow",
    "更亮",
    "同模",
    "加效果",
    "发光",
    "闪光",
    "加闪光",
}


def _parts_not_concrete(text: str) -> bool:
    s = text.strip().lower()
    return s in _EMPTY_PARTS or s in _WEAK_PARTS


def judge_relation_rows(rows: list[LadderRow]) -> tuple[bool, list[str]]:
    """按 art-merge 六条做可机读检查（文字定稿门禁）。"""
    issues: list[str] = []
    # 件数 / 八行已在 parse 保证。合成是否说得通仍由讨论稿判定，这里只拦住空零件和只加光效。
    pcts = [r.scale_pct for r in rows]
    if pcts[0] < 0.55:
        issues.append(f"L1 scale_pct={pcts[0]:.2f} 过低（低档应占格大半，建议 ≥0.58）")
    if pcts[-1] > 0.82:
        issues.append(f"L8 scale_pct={pcts[-1]:.2f} 过高（应留边不顶格，建议 ≤0.80）")
    for i in range(1, 8):
        if pcts[i] <= pcts[i - 1]:
            issues.append(
                f"L{rows[i].level:02d} scale_pct {pcts[i]:.2f} 未大于 L{rows[i-1].level:02d} {pcts[i-1]:.2f}"
            )
        if rows[i].silhouette.lower() == rows[i - 1].silhouette.lower():
            issues.append(
                f"L{rows[i].level:02d} 剪影家族与 L{rows[i-1].level:02d} 相同：{rows[i].silhouette!r}"
            )
        if _parts_not_concrete(rows[i].parts_add):
            issues.append(
                f"L{rows[i].level:02d} 新增零件说不通：{rows[i].parts_add!r}（要具体零件，不能是空、破折号或只加光效）"
            )
    if pcts[-1] < max(pcts[:-1]) + 0.01:
        issues.append("L8 未严格为最大 scale_pct")
    for r in rows:
        if not r.name or not r.silhouette:
            issues.append(f"L{r.level:02d} 物件名或剪影家族为空")
    return (len(issues) == 0, issues)


def _border_median(arr, band: int = 6):
    import numpy as np

    h, w, _ = arr.shape
    band = max(1, min(band, h // 8, w // 8))
    parts = np.concatenate(
        [
            arr[:band].reshape(-1, 3),
            arr[-band:].reshape(-1, 3),
            arr[:, :band].reshape(-1, 3),
            arr[:, -band:].reshape(-1, 3),
        ],
        axis=0,
    )
    return np.median(parts.astype(np.float32), axis=0)


def _subject_distance(arr):
    """每个像素到最近平涂底的距离。底包括外圈，以及内嵌方卡的纸色。"""
    import numpy as np

    bg = _border_median(arr)
    diff = np.linalg.norm(arr.astype(np.float32) - bg, axis=2)
    paper_sel = (diff > 5) & (diff < 22)
    if float(paper_sel.mean()) > 0.12:
        paper = np.median(arr[paper_sel].astype(np.float32), axis=0)
        dist = np.minimum(diff, np.linalg.norm(arr.astype(np.float32) - paper, axis=2))
    else:
        dist = diff
    return dist, bg


def has_inset_card(arr) -> bool:
    """外圈平涂底里嵌着另一块近色矩形（normalize 整图贴上去的方框）。"""
    import numpy as np

    bg = _border_median(arr)
    diff = np.linalg.norm(arr.astype(np.float32) - bg, axis=2)
    h, w = diff.shape
    paper = (diff > 5) & (diff < 22)
    if float(paper.mean()) < 0.12:
        return False
    ys, xs = np.where(paper)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    margin = min(y0, h - 1 - y1, x0, w - 1 - x1)
    if margin < max(4, int(0.03 * min(h, w))):
        return False
    if (y1 - y0) < 0.4 * h or (x1 - x0) < 0.4 * w:
        return False
    box = paper[y0 : y1 + 1, x0 : x1 + 1]
    return float(box.mean()) >= 0.45


def _bbox_fill(im_path: Path) -> tuple[float, float, float]:
    if Image is None:
        raise RuntimeError("需要 Pillow：pip install pillow")
    im = Image.open(im_path).convert("RGB")
    import numpy as np

    arr = np.array(im)
    dist, _bg = _subject_distance(arr)
    mask = dist > 25
    if not mask.any():
        return 0.0, 0.0, 0.0
    h, w = arr.shape[:2]
    ys, xs = np.where(mask)
    bh = (ys.max() - ys.min() + 1) / h
    bw = (xs.max() - xs.min() + 1) / w
    fill = mask.sum() / (h * w)
    return bh, bw, fill


def audit_ladder_dir(
    folder: Path,
    *,
    expected_pcts: list[float] | None = None,
    tol: float = 0.04,
) -> tuple[bool, list[str]]:
    """像素级阶梯审计：框高单调、L8 最大。"""
    issues: list[str] = []
    heights: list[tuple[int, float]] = []
    for i in range(1, 9):
        p = folder / f"L{i:02d}.jpg"
        if not p.is_file():
            p = folder / f"L{i:02d}.png"
        if not p.is_file():
            issues.append(f"缺少 L{i:02d} 方图")
            continue
        bh, _bw, _fill = _bbox_fill(p)
        heights.append((i, bh))
        import numpy as np

        cell = np.array(Image.open(p).convert("RGB"))
        if has_inset_card(cell):
            issues.append(f"L{i:02d} 有内嵌方框（整图贴底，底色接不上）")
        if expected_pcts and i <= len(expected_pcts):
            exp = expected_pcts[i - 1]
            if abs(bh - exp) > tol + 0.08:
                issues.append(
                    f"L{i:02d} bbox_h={bh:.2f} 偏离关系稿 scale_pct={exp:.2f} 过多（>|{tol+0.08:.2f}|）"
                )
    if len(heights) < 8:
        return False, issues
    hs = [h for _, h in heights]
    for i in range(1, 8):
        if hs[i] <= hs[i - 1] - 0.01:
            issues.append(
                f"体量非单调：L{heights[i][0]:02d} h={hs[i]:.2f} ≤ L{heights[i-1][0]:02d} h={hs[i-1]:.2f}"
            )
    if hs[-1] < max(hs[:-1]) - 0.01:
        issues.append(f"L08 框高 {hs[-1]:.2f} 不是全梯最大（max={max(hs):.2f}）")
    return (len(issues) == 0, issues)


def split_sheet_equal_columns(
    sheet: Path,
    out_dir: Path,
    *,
    columns: int = 8,
    size: int = 1024,
) -> list[Path]:
    """16:9 整梯等分 8 列 → 各 1024 方图（object-fit contain 于列内）。"""
    if Image is None:
        raise RuntimeError("需要 Pillow")
    out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(sheet).convert("RGB")
    w, h = im.size
    col_w = w // columns
    written: list[Path] = []
    for i in range(columns):
        x0, x1 = i * col_w, (i + 1) * col_w if i < columns - 1 else w
        cell = im.crop((x0, 0, x1, h))
        placed = place_subject_on_square(cell, 0.70, size)
        dest = out_dir / f"L{i + 1:02d}.jpg"
        placed.save(dest, quality=92)
        written.append(dest)
    return written


def cmd_relation_judge(file_path: Path, track_id: str | None, all_tracks: bool) -> int:
    data = load_phase1(file_path)
    tracks: dict[str, Any] = data["tracks"]
    ids = list(tracks.keys()) if all_tracks or not track_id else [track_id]
    if track_id and track_id not in tracks:
        print(f"未知 track: {track_id}，可选: {', '.join(tracks)}")
        return 1
    any_fail = False
    for tid in ids:
        print(f"\n=== 第一段关系审 · {tid} ===")
        try:
            rows = parse_rows(tracks[tid])
        except ValueError as e:
            print(f"❌ {e}")
            any_fail = True
            continue
        ok, issues = judge_relation_rows(rows)
        if ok:
            print("✅ 六条机读检查通过 → 可标记「文字定稿」并进入关系核对出图")
            for r in rows:
                print(
                    f"  L{r.level:02d} {r.name} | {r.silhouette} | pct={r.scale_pct:.2f} | +{r.parts_add or '—'}"
                )
        else:
            any_fail = True
            print("❌ 未过线：")
            for it in issues:
                print(f"  · {it}")
    return 1 if any_fail else 0


def cmd_audit(folder: Path, phase1: Path | None, track_id: str | None) -> int:
    expected = None
    if phase1 and track_id:
        data = load_phase1(phase1)
        rows = parse_rows(data["tracks"][track_id])
        expected = [r.scale_pct for r in rows]
    ok, issues = audit_ladder_dir(folder, expected_pcts=expected)
    print(f"审计目录: {folder}")
    if ok:
        print("✅ 阶梯体量审计通过")
        return 0
    print("❌ 阶梯体量审计未过：")
    for it in issues:
        print(f"  · {it}")
    return 1


def cmd_split(sheet: Path, out_dir: Path, columns: int) -> int:
    paths = split_sheet_equal_columns(sheet, out_dir, columns=columns)
    print(f"已切 {len(paths)} 格 → {out_dir}")
    for p in paths:
        print(f"  {p}")
    return 0


def place_subject_on_square(im: Image.Image, target_h_ratio: float, size: int = 1024) -> Image.Image:
    """只把前景铺到一块平涂底上。不把原图矩形贴上去，避免内嵌方框，也不把主体裁出格。"""
    import numpy as np

    arr = np.array(im.convert("RGB"))
    dist, bg = _subject_distance(arr)
    alpha = np.clip((dist - 14.0) / 18.0, 0.0, 1.0)
    mask = alpha > 0.15
    h, w = alpha.shape
    if not mask.any():
        color = tuple(int(round(float(c))) for c in bg)
        return Image.new("RGB", (size, size), color)
    ys, xs = np.where(mask)
    sub_h = int(ys.max() - ys.min() + 1)
    sub_w = int(xs.max() - xs.min() + 1)
    pad = 8
    y0, y1 = max(0, int(ys.min()) - pad), min(h - 1, int(ys.max()) + pad)
    x0, x1 = max(0, int(xs.min()) - pad), min(w - 1, int(xs.max()) + pad)
    crop_rgb = arr[y0 : y1 + 1, x0 : x1 + 1]
    crop_a = (alpha[y0 : y1 + 1, x0 : x1 + 1] * 255).astype(np.uint8)
    crop = Image.fromarray(np.dstack([crop_rgb, crop_a]), "RGBA")
    cw, ch = crop.size
    target_h = max(8, int(size * target_h_ratio))
    max_w = size - 8
    scale = min(target_h / max(sub_h, 1), max_w / max(sub_w, 1))
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    color = tuple(int(round(float(c))) for c in bg)
    canvas = Image.new("RGBA", (size, size), color + (255,))
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)
    return canvas.convert("RGB")


def normalize_cell_to_target(im_path: Path, target_h_ratio: float, size: int = 1024) -> None:
    """按关系稿 scale_pct 归一化主体框高（关系核对出图后处理）。"""
    if Image is None:
        raise RuntimeError("需要 Pillow")
    im = Image.open(im_path).convert("RGB")
    place_subject_on_square(im, target_h_ratio, size).save(im_path, quality=92)


def cmd_normalize(folder: Path, phase1: Path, track_id: str, *, max_passes: int = 3) -> int:
    data = load_phase1(phase1)
    rows = parse_rows(data["tracks"][track_id])
    expected = [r.scale_pct for r in rows]
    for attempt in range(1, max_passes + 1):
        for r in rows:
            for ext in (".jpg", ".png"):
                p = folder / f"L{r.level:02d}{ext}"
                if p.is_file():
                    normalize_cell_to_target(p, r.scale_pct)
                    print(f"归一化 L{r.level:02d} → target_h≈{r.scale_pct:.2f}")
                    break
        ok, issues = audit_ladder_dir(folder, expected_pcts=expected)
        if ok:
            print("✅ normalize 后阶梯审计通过")
            return 0
        if attempt < max_passes:
            print(f"⚠️ 第 {attempt} 次 normalize 后仍未过，重试…")
    print("❌ normalize 后阶梯审计仍未过：")
    for it in issues:
        print(f"  · {it}")
    return 1
