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
    evolve_to: str = ""
    merge_why: str = ""


# 6/8：经典合成梯；9/12/15：整表参考常见 3×3 / 4×3 / 5×3
_ALLOWED_LEVELS = {6, 8, 9, 12, 15}


def load_phase1(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "tracks" not in data:
        raise ValueError("phase1 文件需包含 tracks: { id: { rows: [...] } }")
    return data


def _track_levels(track: dict[str, Any], rows_raw: list[Any]) -> int:
    n = int(track.get("levels") or len(rows_raw) or 8)
    if n not in _ALLOWED_LEVELS:
        raise ValueError(f"levels 仅支持 {sorted(_ALLOWED_LEVELS)}，当前 {n}")
    return n


def parse_rows(track: dict[str, Any]) -> list[LadderRow]:
    rows_raw = track.get("rows") or []
    n = _track_levels(track, rows_raw)
    if len(rows_raw) != n:
        raise ValueError(f"必须正好 {n} 行（levels={n}），当前 {len(rows_raw)}")
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
                evolve_to=str(r.get("evolve_to", "")).strip(),
                merge_why=str(r.get("merge_why", "")).strip(),
            )
        )
    out.sort(key=lambda x: x.level)
    if [x.level for x in out] != list(range(1, n + 1)):
        raise ValueError(f"level 必须为 1..{n} 连续")
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



# EN ↔ CJK mother-token aliases so base_body="strawberry soft candy" matches 草莓软糖
TOKEN_ALIASES: dict[str, tuple[str, ...]] = {
    "strawberry": ("strawberry", "草莓"),
    "berry": ("berry", "莓", "草莓"),
    "soft": ("soft", "软", "软糖"),
    "candy": ("candy", "糖", "软糖", "糖果"),
    "gummy": ("gummy", "软糖", "软"),
    "peach": ("peach", "桃", "蜜桃"),
    "apple": ("apple", "苹果"),
    "bottle": ("bottle", "瓶", "药瓶"),
    "potion": ("potion", "药", "药瓶"),
}

_SWAP_SUBJECT_RE = re.compile(
    r"(?:^|[的之\s·])?(开盖|金色|银色|水晶)?(礼盒|奖杯|宝石盒|珠宝盒|首饰盒|糖罐|宝箱|trophy|gift\s*box)",
    re.I,
)


def _token_match_variants(token: str) -> tuple[str, ...]:
    t = (token or "").strip().lower()
    if not t:
        return ()
    return TOKEN_ALIASES.get(t, (t,))


def _base_body_tokens(base_body: str) -> list[str]:
    """Meaningful tokens from base_body for continuity checks (CJK bigrams + latin words)."""
    raw = (base_body or "").strip()
    if not raw:
        return []
    tokens: list[str] = []
    for m in re.finditer(r"[A-Za-z0-9_]{3,}", raw):
        tokens.append(m.group(0).lower())
    # Prefer explicit separators; else sliding bigrams on CJK runs.
    for chunk in re.split(r"[\s·|/＋+，,、；;：:]+", raw):
        chunk = chunk.strip()
        if not chunk:
            continue
        cjk = "".join(ch for ch in chunk if "\u4e00" <= ch <= "\u9fff")
        if len(cjk) >= 2:
            if len(cjk) <= 4:
                tokens.append(cjk)
            else:
                tokens.extend(cjk[i : i + 2] for i in range(0, len(cjk) - 1, 2))
    # de-dup preserve order
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        if t and t not in seen and t not in {"基档", "物件", "道具"}:
            seen.add(t)
            out.append(t)
    return out[:12]


def judge_relation_rows(
    rows: list[LadderRow],
    track: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """按 art-merge 六条做可机读检查（文字定稿门禁）。"""
    track = track or {}
    issues: list[str] = []
    n = len(rows)
    chain_mode = str(track.get("chain_mode") or "").strip()
    if chain_mode and chain_mode not in {"same_object", "shop_ladder", "species_change"}:
        issues.append(f"chain_mode 非法：{chain_mode!r}（same_object|shop_ladder|species_change）")

    # 软糖/糖纸类省略 chain_mode 不允许走轻门（勿把 pastel candy brand 等画风词误判成糖果链）
    candy_blob = " ".join(
        [
            str(track.get("base_body") or ""),
            *[
                f"{getattr(r, 'name', '')} {getattr(r, 'silhouette', '')} {getattr(r, 'evolve_to', '')}"
                for r in rows
            ],
        ]
    )
    if (not chain_mode) and re.search(
        r"(软糖|草莓糖|棒棒糖|糖纸|硬糖|gummy|soft\s*candy)", candy_blob, re.I
    ):
        issues.append(
            "软糖/糖纸类省略 chain_mode 不允许：须显式 shop_ladder（同族形变）；轻门仅用于非糖果链"
        )

    # 件数已在 parse 保证。合成是否说得通仍由讨论稿判定。
    # 体量：竞品常不单调放大；只硬拦末档明显矮、剪影复读；scale 极端才拦。
    pcts = [r.scale_pct for r in rows]
    if pcts[0] < 0.45:
        issues.append(f"L1 scale_pct={pcts[0]:.2f} 过低（缩略难认，建议 ≥0.50）")
    if pcts[-1] > 0.98:
        issues.append(f"L{n} scale_pct={pcts[-1]:.2f} 过高（易超框切顶，建议 ≤0.95）")
    if pcts[-1] + 0.08 < max(pcts):
        issues.append(
            f"L{n} scale_pct={pcts[-1]:.2f} 明显小于前档最大 {max(pcts):.2f}"
        )
    for i in range(1, n):
        if rows[i].silhouette.lower() == rows[i - 1].silhouette.lower():
            issues.append(
                f"L{rows[i].level:02d} 剪影家族与 L{rows[i-1].level:02d} 相同：{rows[i].silhouette!r}"
            )
        # same_object（默认轻门）：继续要求具体 parts_add
        # shop/species：允许 parts_add 为空，改看 evolve_to + merge_why
        if chain_mode in {"", "same_object"} and _parts_not_concrete(rows[i].parts_add):
            issues.append(
                f"L{rows[i].level:02d} 新增零件说不通：{rows[i].parts_add!r}（要具体零件，不能是空、破折号或只加光效）"
            )
    for r in rows:
        if not r.name or not r.silhouette:
            issues.append(f"L{r.level:02d} 物件名或剪影家族为空")

    # Optional but sticky: same-object ladders declare base_body so later tiers cannot reinvent the mother mesh.
    # Species-change / shop_ladder omit base_body.
    base_body = str(track.get("base_body") or "").strip()
    if chain_mode == "same_object" and not base_body:
        issues.append("chain_mode=same_object 时必须填写 base_body")
    if chain_mode in {"shop_ladder", "species_change"} and base_body:
        issues.append(f"chain_mode={chain_mode} 不应填写 base_body（当前 {base_body!r}）")
    if base_body:
        tokens = _base_body_tokens(base_body)
        if not tokens:
            issues.append(f"base_body 无法抽出可核验词：{base_body!r}")
        else:
            need = 1 if len(tokens) == 1 else min(2, len(tokens))
            for r in rows:
                blob = f"{r.silhouette} {r.name}".lower()
                hits = [
                    t
                    for t in tokens
                    if any(v.lower() in blob for v in _token_match_variants(t))
                ]
                if len(hits) < need:
                    issues.append(
                        f"L{r.level:02d} 未锁母体 base_body={base_body!r}："
                        f"silhouette/name 需保留母体词 {tokens[:4]}（命中 {hits or '无'}）"
                    )

    # same_object：禁止剪影/名称以礼盒奖杯等换货容器作主语（应走 shop_ladder）
    if chain_mode == "same_object":
        for r in rows:
            for field_name, text in (("silhouette", r.silhouette), ("name", r.name), ("parts_add", r.parts_add)):
                s = (text or "").strip()
                if not s or s in {"—", "-", "－"}:
                    continue
                # 零件上挂小礼盒/小奖杯饰件 OK；主语换货不行
                if field_name == "parts_add" and re.search(r"(小|迷你|微型).{0,4}(礼盒|奖杯)", s):
                    continue
                m = _SWAP_SUBJECT_RE.search(s)
                if not m:
                    continue
                # 母体上的配件短语（草莓软糖上的小礼盒）放行：母体词在换货词之前
                mother_before = False
                if base_body:
                    for t in _base_body_tokens(base_body):
                        for v in _token_match_variants(t):
                            pos = s.lower().find(v.lower())
                            if pos >= 0 and pos < m.start():
                                mother_before = True
                                break
                        if mother_before:
                            break
                if mother_before and field_name != "silhouette":
                    continue
                # 剪影以换货容器起头/盛装母体 → 换货
                if field_name == "silhouette" or (
                    field_name == "name" and re.search(r"^(开盖|金色|银色)?(礼盒|奖杯)", s)
                ):
                    issues.append(
                        f"L{r.level:02d} same_object 换货主语：{field_name}={s!r} "
                        f"以礼盒/奖杯等作主体；应改 shop_ladder 同族形变，或改成母体上的配件"
                    )
                    break

    # shop_ladder / species_change：叙事闸（MergePerCell 轻门不强制 merge_why；仅这两种链型启用）
    if chain_mode in {"shop_ladder", "species_change"}:
        weak_why = {"", "—", "-", "－", "更华丽", "更高级", "升级", "更好", "none"}
        seen_evolve: list[str] = []
        for r in rows:
            if not r.evolve_to:
                issues.append(f"L{r.level:02d} chain_mode={chain_mode} 缺少 evolve_to")
            else:
                key = r.evolve_to.strip().lower()
                if key in seen_evolve:
                    issues.append(f"L{r.level:02d} evolve_to 回退/重复：{r.evolve_to!r}")
                seen_evolve.append(key)
            if r.level == 1:
                continue
            why = (r.merge_why or "").strip().lower()
            if why in weak_why or why in _WEAK_PARTS:
                issues.append(
                    f"L{r.level:02d} merge_why 说不通：{r.merge_why!r}（要具体合成理由）"
                )
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
    """像素级阶梯审计：框高单调、末档最大。档数跟 expected_pcts，缺省仍按 8。"""
    issues: list[str] = []
    heights: list[tuple[int, float]] = []
    n = len(expected_pcts) if expected_pcts else 8
    if n < 2:
        return False, ["expected_pcts 至少 2 档"]
    for i in range(1, n + 1):
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
    if len(heights) < n:
        return False, issues
    hs = [h for _, h in heights]
    for i in range(1, n):
        if hs[i] <= hs[i - 1] - 0.01:
            issues.append(
                f"体量非单调：L{heights[i][0]:02d} h={hs[i]:.2f} ≤ L{heights[i-1][0]:02d} h={hs[i-1]:.2f}"
            )
    if hs[-1] < max(hs[:-1]) - 0.01:
        issues.append(f"L{n:02d} 框高 {hs[-1]:.2f} 不是全梯最大（max={max(hs):.2f}）")
    return (len(issues) == 0, issues)


_STYLE_OPT_OUT = (
    "写实",
    "照片",
    "摄影",
    "水彩",
    "赛博",
    "像素",
    "厚涂",
    "扁平",
    "矢量",
    "油画",
    "黏土",
    "石膏",
    "皮克斯",
)
_MERGE_SURFACE = (
    "休闲 merge 货柜默认气质：Gossip Harbor 玩具货柜卡通——"
    "光泽卡通 3D、圆润厚实、无硬描边、暖饱和、柔光渐变、糖釉玩具高光、棋盘缩略一眼可认。"
    "材质锁死为卡通玩具/糖釉道具，不是实物。"
    "禁止：写实摄影、美食棚拍、产品静物、玻璃真实折射、木纹指纹、果汁乳浊摄影感、"
    "微距毛孔、油光金属、暗沉旧塑料。"
    "整表参考只锁格子版式，不跟参考写实表面。"
)
# 邻档框高差小于此值时只出提示（竞品本身常不单调放大）。
OVERVIEW_MIN_STEP = 0.04
# 末档比全表最高矮过此值，才算「明显小于前档」硬伤。
OVERVIEW_LAST_SHRINK = 0.08


def player_named_style(*texts: str) -> bool:
    blob = "\n".join(texts)
    return any(word in blob for word in _STYLE_OPT_OUT)


def _has_full_merge_surface_lock(blob: str) -> bool:
    """完整默认锁已在文中：须含材质锁死 + 禁写实硬句，不能只靠「棋盘缩略」等零散词。"""
    text = str(blob or "")
    if "材质锁死" not in text:
        return False
    if "写实摄影" not in text and "美食棚拍" not in text:
        return False
    return "卡通玩具" in text or "糖釉" in text or "玻璃真实折射" in text


def merge_surface_lock_line(goal: str = "", prompt: str = "") -> str:
    """没写风格时钉 Gossip Harbor 玩具货柜。

    点名风格只看 goal（玩家原话），不看含 Warm-Start 的 prompt——
    taste「避开赛博霓虹」曾因词表命中「赛博」被当成玩家点名赛博，整段锁留空。
    完整硬句是否已在，才看 prompt；零散「棋盘缩略 / Gossip Harbor」不够跳过。
    """
    if player_named_style(goal):
        return ""
    if _has_full_merge_surface_lock(prompt):
        return ""
    return _MERGE_SURFACE


def _erode_mask_once(mask):
    """去掉 1px AA 毛边，避免奶油卡边缘被当成主体。"""
    import numpy as np

    if mask.shape[0] < 3 or mask.shape[1] < 3:
        return mask
    out = mask.copy()
    out[1:-1, 1:-1] = (
        mask[1:-1, 1:-1]
        & mask[:-2, 1:-1]
        & mask[2:, 1:-1]
        & mask[1:-1, :-2]
        & mask[1:-1, 2:]
    )
    return out


def _largest_blob_stats(mask) -> tuple[int, int, int] | None:
    """最大连通域：(面积, y0, y1)。"""
    import numpy as np
    from collections import deque

    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best: tuple[int, int, int] | None = None  # area, y0, y1
    for y in range(h):
        xs = np.where(mask[y] & ~seen[y])[0]
        for x in xs:
            if seen[y, x]:
                continue
            q: deque[tuple[int, int]] = deque([(y, x)])
            seen[y, x] = True
            y0 = y1 = y
            area = 0
            while q:
                cy, cx = q.popleft()
                area += 1
                if cy < y0:
                    y0 = cy
                if cy > y1:
                    y1 = cy
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if best is None or area > best[0]:
                best = (area, y0, y1)
    return best


def _largest_blob_yrange(mask) -> tuple[int, int] | None:
    """最大连通域的纵向范围。浅色卡上的物件框高必须取最大块，不能用全 mask bbox。"""
    best = _largest_blob_stats(mask)
    if best is None:
        return None
    return best[1], best[2]


def _largest_row_run_yrange(mask) -> tuple[int, int] | None:
    """mask 行占用的最长连续纵向带（柔影切碎连通域时的回退）。"""
    occ = mask.mean(axis=1) > 0.01
    best: list[int] | None = None
    cur: list[int] | None = None
    for y, on in enumerate(occ):
        if on:
            if cur is None:
                cur = [y, y]
            else:
                cur[1] = y
        elif cur is not None:
            if best is None or (cur[1] - cur[0]) > (best[1] - best[0]):
                best = cur
            cur = None
    if cur is not None and (best is None or (cur[1] - cur[0]) > (best[1] - best[0])):
        best = cur
    if best is None:
        return None
    return best[0], best[1]


def _cell_subject_mask(cell):
    """格内物件 mask。有浅色圆角卡时先按卡内色剥卡，再量物件；无卡则相对格缝底。

    旧逻辑只用格边缘中位色，奶油/浅灰卡会被当成主体，框高≈1.0，残片闸也半盲。
    """
    import numpy as np

    h, w = cell.shape[:2]
    if h < 8 or w < 8:
        return np.zeros((max(h, 1), max(w, 1)), dtype=bool)
    rgb = cell.astype(np.float32)
    band = max(1, min(4, h // 10, w // 10))
    seam = _border_median(cell, band=band)
    dist_seam = np.linalg.norm(rgb - seam, axis=2)
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    # 卡心取样：格内缩进后的高亮低彩区域 ≈ 奶油/浅灰/粉卡纸色
    inset = max(3, int(0.12 * min(h, w)))
    interior = np.zeros((h, w), dtype=bool)
    if h > 2 * inset and w > 2 * inset:
        interior[inset : h - inset, inset : w - inset] = True
    paper_sel = interior & (lum > 215) & (chroma < 50)
    if float(paper_sel.mean()) < 0.02:
        paper_sel = interior & (lum > 200) & (chroma < 70)
    if float(paper_sel.mean()) < 0.01:
        # 无内嵌浅色卡：相对格缝底，再去掉近白平涂
        content = dist_seam > 28
        white = (rgb.min(axis=2) > 214) & (chroma < 28)
        subject = content & ~white
        if float(subject.mean()) < 0.008:
            subject = content
        return subject

    paper = np.median(rgb[paper_sel], axis=0)
    dist_paper = np.linalg.norm(rgb - paper, axis=2)
    paper_l = float(0.299 * paper[0] + 0.587 * paper[1] + 0.114 * paper[2])
    paper_c = float(paper.max() - paper.min())
    # 柔影：同色相、比卡纸更暗（可更饱和一点）。暖桃色投影 chroma>30，旧「chroma<30」去不掉。
    soft_shadow = _soft_card_shadow_mask(rgb, lum, chroma, paper, paper_l, paper_c, dist_paper)
    subject = (
        (dist_paper > 34)
        & (dist_seam > 12)
        & ~soft_shadow
        & ~((lum > 230) & (chroma < 35))
    )
    if float(subject.mean()) < 0.004:
        # 剥卡过狠时回退：相对卡纸色、保留缝外抑制
        subject = (dist_paper > 28) & (dist_seam > 10)
    return subject


def _soft_card_shadow_mask(rgb, lum, chroma, paper, paper_l: float, paper_c: float, dist_paper):
    """卡上投影：与卡纸同色相、更暗；允许比卡纸更饱和。"""
    import numpy as np

    darker = lum < (paper_l - 4)
    near = dist_paper < 72
    if paper_c < 10:
        # 近灰卡纸：色相不稳，退回低彩暗区
        return darker & near & (chroma < 36)
    # 色度方向与卡纸接近（忽略亮度）
    paper_vec = paper.astype(np.float32) - float(np.mean(paper))
    pix_vec = rgb - lum[..., None]
    p_norm = float(np.linalg.norm(paper_vec)) + 1e-6
    pix_norm = np.linalg.norm(pix_vec, axis=2) + 1e-6
    cos = (pix_vec * paper_vec).sum(axis=2) / (pix_norm * p_norm)
    same_hue = cos > 0.55
    return darker & near & same_hue


def _seam_subject_mask(cell):
    """相对格缝底的旧物件 mask。剥卡后切边变钝时，残片平切仍靠它召回。"""
    import numpy as np

    h, w = cell.shape[:2]
    if h < 8 or w < 8:
        return np.zeros((max(h, 1), max(w, 1)), dtype=bool)
    rgb = cell.astype(np.float32)
    bg = _border_median(cell, band=max(1, min(4, h // 10, w // 10)))
    content = np.linalg.norm(rgb - bg, axis=2) > 28
    white = (rgb.min(axis=2) > 214) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 28)
    subject = content & ~white
    if float(subject.mean()) < 0.008:
        subject = content
    return subject


def _cell_subject_height_ratio(cell) -> float:
    """格内物件框高 / 格高。浅色圆角卡与卡上暖色投影不算主体。"""
    h = int(cell.shape[0])
    if h < 8:
        return 0.0
    subject = _cell_subject_mask(cell)
    eroded = _erode_mask_once(subject)
    use = eroded if eroded.any() else subject
    if not use.any():
        return 0.0
    stats = _largest_blob_stats(use)
    if stats is None:
        return 0.0
    area, y0, y1 = stats
    total = int(use.sum())
    # 柔影若把果酱碗等实心物件切成多块，最大连通域会偏矮；改用行占用最长带。
    if total > 0 and area < 0.55 * total:
        yrange = _largest_row_run_yrange(use)
        if yrange is not None:
            y0, y1 = yrange
    return float(y1 - y0 + 1) / float(h)


def _fragment_score_on_mask(content, h: int, w: int) -> float:
    """在给定物件 mask 上找贴边/切平残片面积占比。"""
    import numpy as np

    if content is None or not content.any():
        return 0.0
    occ = content.mean(axis=1) > 0.01
    bands: list[list[int]] = []
    gap = max(2, h // 25)
    for y, on in enumerate(occ):
        if not on:
            continue
        if not bands or y - bands[-1][1] > gap:
            bands.append([y, y])
        else:
            bands[-1][1] = y
    if len(bands) < 2:
        return 0.0
    # 只忽略「很薄」的外圈碎带（卡边 AA）。有面积的贴边残片必须保留——拼贴残片本就贴边。
    edge = max(2, h // 40)
    thin = max(2, h // 35)
    areas = [float(content[a : b + 1].sum()) / float(h * w) for a, b in bands]
    main = max(range(len(bands)), key=lambda i: areas[i])
    worst = 0.0
    for i, (y0, y1) in enumerate(bands):
        if i == main or areas[i] < 0.01:
            continue
        band_h = y1 - y0 + 1
        wholly_edge = y1 < edge or y0 > h - 1 - edge
        if wholly_edge and band_h <= thin and areas[i] < 0.02:
            continue
        cols = np.where(content[y0 : y1 + 1].any(axis=0))[0]
        if cols.size == 0:
            continue
        span = int(cols.max() - cols.min() + 1)
        if span < 1:
            continue
        top = content[y0 : y0 + 2, cols.min() : cols.max() + 1].any(axis=0).sum() / span
        bot = content[y1 - 1 : y1 + 1, cols.min() : cols.max() + 1].any(axis=0).sum() / span
        if max(top, bot) >= 0.9:
            worst = max(worst, areas[i])
    return worst


def _cell_fragment_rows(cell) -> float:
    """格内与主体分离、顶或底被一刀切平的残片面积占比。抠格拼贴常留这种半截物件。

    剥卡 mask 负责浅色卡场景；格缝 mask 负责召回平切残片（剥卡后切边常变钝）。
    取两者较大值。
    """
    h, w = cell.shape[:2]
    if h < 16 or w < 8:
        return 0.0
    peeled = _cell_subject_mask(cell)
    # 残片不腐蚀：腐蚀会把平切边啃钝，管乐 L6 一类 0.04 残片会漏掉。
    peel_score = _fragment_score_on_mask(peeled, h, w)
    seam_score = _fragment_score_on_mask(_seam_subject_mask(cell), h, w)
    return max(peel_score, seam_score)


def audit_overview_sheet(
    image_path: Path,
    *,
    rows: int = 2,
    cols: int = 4,
    min_step: float = OVERVIEW_MIN_STEP,
    last_shrink: float = OVERVIEW_LAST_SHRINK,
) -> tuple[bool, list[str]]:
    """整表像素审阅。

    硬伤（ok=False）：缺主体；贴边残片/切顶拼贴；末档明显矮于全表最高。
    提示（以「提示：」开头，不单独让 ok=False）：邻档框高接近、末档略非最大。
    分档应靠剪影/件数/容器/完成态；禁止为过闸跨轮抠格拼表。
    """
    hard: list[str] = []
    soft: list[str] = []
    if Image is None:
        return False, ["需要 Pillow 才能审整表体量"]
    if rows < 1 or cols < 1 or rows * cols < 2:
        return False, ["整表行列至少 2 格"]
    path = Path(image_path)
    if not path.is_file():
        return False, [f"整表不存在：{path}"]
    im = Image.open(path).convert("RGB")
    import numpy as np

    arr = np.array(im)
    h, w = arr.shape[:2]
    heights: list[float] = []
    for r in range(rows):
        y0, y1 = (h * r) // rows, (h * (r + 1)) // rows
        for c in range(cols):
            x0, x1 = (w * c) // cols, (w * (c + 1)) // cols
            cell = arr[y0:y1, x0:x1]
            ratio = _cell_subject_height_ratio(cell)
            heights.append(ratio)
            if ratio < 0.08:
                hard.append(f"第 {len(heights)} 格没有量到主体")
            frag = _cell_fragment_rows(cell)
            if frag > 0:
                hard.append(
                    f"第 {len(heights)} 格有贴边残片（面积 {frag:.3f}）："
                    "像抠格拼贴或切顶，整张重出，禁止拼贴"
                )
    for i in range(1, len(heights)):
        delta = heights[i] - heights[i - 1]
        if delta < min_step:
            soft.append(
                f"提示：邻档框高接近（第 {i}→{i + 1} 为 "
                f"{heights[i - 1]:.2f}→{heights[i]:.2f}）；"
                "分档靠剪影/件数，勿跨轮抠格拼表凑体量阶梯"
            )
    if heights:
        peak = max(heights)
        last = heights[-1]
        # 用两位小数比「明显矮」，避免 0.081 vs 0.08 的浮点擦边误杀干净浅色卡整表。
        shrink = round(peak - last, 2)
        if shrink > round(last_shrink, 2):
            hard.append(
                f"末档明显小于前档：末格 {last:.2f}，最大 {peak:.2f}"
            )
        elif shrink >= 0.01:
            soft.append(
                f"提示：末档不是最大（末格 {last:.2f}，最大 {peak:.2f}）；"
                "可接受，只要剪影/件数可分且无拼贴残片"
            )
    return (len(hard) == 0, hard + soft)


def cell_to_square_contain(im: Image.Image, size: int = 1024) -> Image.Image:
    """整格 contain 进方图，不单独抽主体缩放，保住组内体量关系。"""
    import numpy as np

    rgb = im.convert("RGB")
    arr = np.array(rgb)
    bg = _border_median(arr)
    color = tuple(int(round(float(c))) for c in bg)
    w, h = rgb.size
    scale = min(size / max(w, 1), size / max(h, 1))
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), color)
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2))
    return canvas



def _tile_fill_color(arr):
    """棋盘格底色：有内嵌方卡就用卡纸色，否则用外圈底。"""
    import numpy as np

    bg = _border_median(arr)
    diff = np.linalg.norm(arr.astype(np.float32) - bg, axis=2)
    paper_sel = (diff > 5) & (diff < 22)
    if float(paper_sel.mean()) > 0.12:
        return np.median(arr[paper_sel].astype(np.float32), axis=0)
    return bg



def cell_to_equal_square(im: Image.Image, size: int = 1024) -> Image.Image:
    """抽出主体（不要内嵌方卡），铺到平涂正方形正中。展陈格里必须居中。"""
    import numpy as np

    rgb = im.convert("RGB")
    arr = np.array(rgb)
    dist, _bg = _subject_distance(arr)
    mask = dist > 25
    if not mask.any():
        return cell_to_square_contain(rgb, size)
    h, w = mask.shape
    ys, xs = np.where(mask)
    sub_h = int(ys.max() - ys.min() + 1)
    sub_w = int(xs.max() - xs.min() + 1)
    occ = max(sub_h / max(h, 1), sub_w / max(w, 1))
    occ = float(np.clip(occ, 0.56, 0.82))
    return place_subject_on_square(rgb, occ, size)



def square_grid_boxes(
    width: int,
    height: int,
    *,
    rows: int = 2,
    columns: int = 4,
) -> list[tuple[int, int, int, int]]:
    """16:9 画布里嵌 2×4 个相同正方形格，上下或左右留边。"""
    if rows < 1 or columns < 1:
        raise ValueError("rows/columns 必须 ≥1")
    side = min(width / columns, height / rows)
    grid_w = side * columns
    grid_h = side * rows
    ox = (width - grid_w) / 2.0
    oy = (height - grid_h) / 2.0
    boxes: list[tuple[int, int, int, int]] = []
    for r in range(rows):
        for c in range(columns):
            x0 = ox + c * side
            y0 = oy + r * side
            boxes.append((int(round(x0)), int(round(y0)), int(round(x0 + side)), int(round(y0 + side))))
    return boxes



def split_sheet_grid(
    sheet: Path,
    out_dir: Path,
    *,
    rows: int = 2,
    columns: int = 4,
    size: int = 1024,
) -> list[Path]:
    """组图 2×4 格 → 八张 1024 方图。

    生成合同是 8 个相同正方形格。16:9 画布上若模型把格铺满，先取 2×4 整格
    再 contain 进正方形，避免把花、旗鳍、糖葫芦签切掉。
    """
    if Image is None:
        raise RuntimeError("需要 Pillow")
    if rows < 1 or columns < 1 or rows * columns != 8:
        raise ValueError("整梯切格必须正好 8 格（默认 rows=2 columns=4）")
    out_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(sheet).convert("RGB")
    w, h = im.size
    written: list[Path] = []
    cw, ch = w // columns, h // rows
    n = 0
    for r in range(rows):
        for c in range(columns):
            n += 1
            x0, y0 = c * cw, r * ch
            x1 = (c + 1) * cw if c < columns - 1 else w
            y1 = (r + 1) * ch if r < rows - 1 else h
            inset = max(2, int(0.05 * min(x1 - x0, y1 - y0)))
            cell = im.crop((x0 + inset, y0 + inset, x1 - inset, y1 - inset))
            dest = out_dir / f"L{n:02d}.jpg"
            # 只居中一次。再调用会把已经摆正的方图按主体占比再缩一次，构图被挪走。
            cell_to_equal_square(cell, size).save(dest, quality=92)
            written.append(dest)
    return written



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
        ok, issues = judge_relation_rows(rows, track=tracks[tid])
        if ok:
            mode = str(tracks[tid].get("chain_mode") or "same_object(default)")
            print(f"✅ 机读检查通过（chain_mode={mode}）→ 可标记「文字定稿」并进入出图")
            for r in rows:
                extra = r.evolve_to or r.parts_add or "—"
                print(
                    f"  L{r.level:02d} {r.name} | {r.silhouette} | pct={r.scale_pct:.2f} | {extra}"
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


def cmd_split(sheet: Path, out_dir: Path, columns: int, rows: int = 1) -> int:
    if rows <= 1:
        paths = split_sheet_equal_columns(sheet, out_dir, columns=columns)
    else:
        paths = split_sheet_grid(sheet, out_dir, rows=rows, columns=columns)
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
