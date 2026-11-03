# -*- coding: utf-8 -*-
"""Job directory helpers: plan / truth / status I/O."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from .defaults import SIZE_BUCKETS, QUALITY_BY_AREA, ALLOWED_SIZES


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class Job:
    def __init__(self, root: Path):
        self.root = root.resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"job dir not found: {self.root}")

    @property
    def plan_path(self) -> Path:
        return self.root / "split_plan.json"

    @property
    def truth_path(self) -> Path:
        return self.root / "truth_boxes.json"

    @property
    def status_path(self) -> Path:
        return self.root / "layer_status.json"

    @property
    def placements_path(self) -> Path:
        return self.root / "_placements.json"

    @property
    def crops_dir(self) -> Path:
        return self.root / "_crops"

    @property
    def new_dir(self) -> Path:
        return self.root / "new"

    @property
    def trim_dir(self) -> Path:
        return self.root / "new_trim"

    def load_plan(self) -> dict:
        if not self.plan_path.exists():
            raise FileNotFoundError(f"missing {self.plan_path}")
        return load_json(self.plan_path)

    def save_plan(self, plan: dict) -> None:
        save_json(self.plan_path, plan)

    def load_truth(self) -> dict:
        if not self.truth_path.exists():
            raise FileNotFoundError(f"missing {self.truth_path} — run setup/calibrate first")
        return load_json(self.truth_path)

    def save_truth(self, truth: dict) -> None:
        save_json(self.truth_path, truth)

    def load_status(self) -> dict:
        if self.status_path.exists():
            return load_json(self.status_path)
        return {"layers": {}, "version": 1}

    def save_status(self, status: dict) -> None:
        save_json(self.status_path, status)

    def ref_path(self, plan: dict | None = None) -> Path:
        plan = plan or self.load_plan()
        name = plan.get("ref") or "ref_full.jpg"
        p = self.root / name
        if not p.exists():
            for cand in ("ref_full.png", "ref_full.jpg", "ref_new_full.jpg"):
                q = self.root / cand
                if q.exists():
                    return q
            raise FileNotFoundError(f"ref image missing under {self.root}")
        return p

    def open_ref(self, plan: dict | None = None) -> Image.Image:
        return Image.open(self.ref_path(plan)).convert("RGBA")


def modules_of(plan: dict) -> list[dict]:
    return list(plan.get("modules") or plan.get("layers") or [])


def size_for_pixel_aspect(pa: float) -> str:
    for upper, size in SIZE_BUCKETS:
        if upper is None or pa < upper:
            return size
    return "1024x1024"


def quality_for_area(area_frac: float) -> str:
    for upper, q in QUALITY_BY_AREA:
        if upper is None or area_frac < upper:
            return q
    return "high"


def pixel_aspect(norm_w: float, norm_h: float, canvas_w: int, canvas_h: int) -> float:
    if not norm_h:
        return 1.0
    return (norm_w / norm_h) * (canvas_w / canvas_h)


def assert_allowed_size(size: str) -> str:
    if size not in ALLOWED_SIZES:
        raise ValueError(f"size {size!r} not in {ALLOWED_SIZES}")
    return size
