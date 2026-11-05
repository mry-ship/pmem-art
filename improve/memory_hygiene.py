"""Memory hygiene: detach missing assets, prune junk candidates, specs/taste/archive."""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from ._time import _now_cst

MEMORY_DIR = ".memory-art"

_JUNK_LEAF = re.compile(
    r"^(?:\d+[a-z]?|r\d+|ref|compose|ghost|crop|diff|random|ping\d*|tmp|temp|new|old|final|layers?|"
    r"shed|hay|trough|fence|barn|farmer|pathsheep|tiresheep|watertire|tire|reconstructed|"
    r"alt|flip|path|edit|compare|overview|truck|leaves|flower|flying|food|mole|mushrooms|pond|"
    r"treehouse|violinist|christmas)$",
    re.I,
)
_JUNK_FOLDER_BITS = (
    "/layers/",
    "/_work/",
    "/crops/",
    "fairy_split",
    "/reconstructed/",
    "/old/",
    "/new/",
)


def is_noise_candidate(module_id: str, folder: str = "") -> bool:
    """True for sync junk: numeric leaves, layer exports, misc scrap folders."""
    mid = (module_id or "").strip()
    if not mid or "." not in mid:
        return True
    leaf = mid.split(".")[-1]
    if _JUNK_LEAF.match(leaf):
        return True
    fold = (folder or "").replace("\\", "/").lower()
    if any(b in fold for b in _JUNK_FOLDER_BITS):
        return True
    # misc.* candidates are almost always scrap folders — never auto-backlog them.
    if mid.startswith("misc."):
        return True
    # Tiny alphanumeric leaves (7b, r1, v2) under character/scene are layer exports.
    if re.fullmatch(r"[a-z]*\d+[a-z]*", leaf, re.I) and len(leaf) <= 4:
        return True
    return False


def prune_noise_candidates(root: Path) -> dict[str, Any]:
    from lifecycle import load_candidates_file, save_candidates_file

    items = load_candidates_file(root)
    keep: list[dict[str, Any]] = []
    dropped: list[str] = []
    for c in items:
        mid = str(c.get("module_id") or "")
        folder = str(c.get("folder") or "")
        if is_noise_candidate(mid, folder):
            dropped.append(mid)
        else:
            keep.append(c)
    save_candidates_file(root, keep)
    return {"before": len(items), "after": len(keep), "dropped": dropped}


def _split_entry_md(text: str) -> tuple[str, str, str] | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]


def _dump_assets_yaml(assets: list[dict[str, Any]]) -> str:
    lines = ["assets:"]
    for a in assets:
        if not isinstance(a, dict):
            continue
        lines.append("  -")
        for key in ("path", "detached_path", "role", "caption", "sha256_16"):
            if key not in a or a[key] in (None, ""):
                continue
            val = a[key]
            if key in ("caption",) or isinstance(val, str) and (":" in val or "#" in val or val.startswith("[") or "\n" in val):
                lines.append(f"    {key}: {json.dumps(str(val), ensure_ascii=False)}")
            else:
                lines.append(f"    {key}: {val}")
    return "\n".join(lines) + "\n"


def detach_missing_assets(root: Path, *, apply: bool = True) -> dict[str, Any]:
    """Rewrite entry frontmatter: missing path → role=detached + detached_path, drop live path."""
    from lifecycle import iter_md_files
    from pmem_art import load_yaml

    entries_dir = root / MEMORY_DIR / "entries"
    touched = 0
    detached_links = 0
    samples: list[str] = []
    if not entries_dir.is_dir():
        return {"touched": 0, "detached_links": 0, "samples": []}

    for md in iter_md_files(entries_dir, recursive=True):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        split = _split_entry_md(text)
        if not split:
            continue
        _pre, fm_raw, body = split
        try:
            fm = load_yaml(fm_raw)
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue
        assets = list(fm.get("assets") or [])
        if not assets:
            continue
        changed = False
        new_assets: list[dict[str, Any]] = []
        for a in assets:
            if not isinstance(a, dict):
                continue
            role = str(a.get("role") or "")
            if role in ("detached", "rejected", "draft_violation"):
                new_assets.append(a)
                continue
            ap = str(a.get("path") or "").replace("\\", "/")
            if not ap:
                new_assets.append(a)
                continue
            if (root / ap).is_file():
                new_assets.append(a)
                continue
            na = dict(a)
            na["role"] = "detached"
            na["detached_path"] = ap
            na.pop("path", None)
            new_assets.append(na)
            changed = True
            detached_links += 1
        if not changed:
            continue
        touched += 1
        samples.append(md.relative_to(root).as_posix())
        if not apply:
            continue
        # Prefer rewriting only the assets: block to avoid disturbing ai_params / long fields.
        fm_text = fm_raw
        assets_yaml = _dump_assets_yaml(new_assets)
        if re.search(r"(?ms)^assets:\n", fm_text):
            fm_new, nsub = re.subn(
                r"(?ms)^assets:\n(?:[ \t]+-.*\n(?:[ \t]{2,}.*\n)*)*",
                assets_yaml,
                fm_text,
                count=1,
            )
            if nsub:
                fm_text = fm_new
            else:
                fm_text = fm_text.rstrip() + "\n" + assets_yaml
        else:
            fm_text = fm_text.rstrip() + "\n" + assets_yaml
        if not fm_text.startswith("\n"):
            fm_text = "\n" + fm_text.lstrip("\n")
        if not fm_text.endswith("\n"):
            fm_text += "\n"
        md.write_text(f"---{fm_text}---{body}", encoding="utf-8")

    return {"touched": touched, "detached_links": detached_links, "samples": samples[:20], "apply": apply}


def ensure_short_specs(root: Path, data: dict[str, Any], *, min_entries: int = 3) -> dict[str, Any]:
    """Create short 视觉设定.md for long-lived modules that have entries but no specs dir."""
    specs_root = root / MEMORY_DIR / "specs"
    specs_root.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    summaries: dict[str, list[str]] = {}
    for e in data.get("entries") or []:
        mid = str(e.get("module") or "")
        if not mid:
            continue
        counts[mid] += 1
        sm = str(e.get("summary") or "").strip()
        if sm and len(summaries.setdefault(mid, [])) < 3:
            summaries[mid].append(sm[:120])

    created: list[str] = []
    skipped: list[str] = []
    for mid, n in sorted(counts.items()):
        if n < min_entries:
            skipped.append(mid)
            continue
        d = specs_root / mid
        vision = d / "视觉设定.md"
        if vision.is_file():
            continue
        d.mkdir(parents=True, exist_ok=True)
        bullets = summaries.get(mid) or ["（从近期 recipe/红线沉淀，图可删，以文字为准）"]
        body = (
            f"# {mid} · 视觉设定\n\n"
            f"长期复用模块（entries≥{min_entries}）。资产可删；以 entries 文字结论为准。\n\n"
            "## 近期要点\n"
            + "\n".join(f"- {b}" for b in bullets)
            + "\n\n## 资产台账\n资产常删；缺图时条目应 `role: detached`，勿把缺图当成文字 STALE。\n"
        )
        vision.write_text(body, encoding="utf-8")
        ledger = d / "资产台账.md"
        if not ledger.is_file():
            ledger.write_text(
                f"# {mid} · 资产台账\n\n以 entries 内 path / detached_path 为准；不强制磁盘留图。\n",
                encoding="utf-8",
            )
        created.append(mid)
    return {"created": created, "skipped_short": skipped, "min_entries": min_entries}


def dedupe_taste_phrases(root: Path) -> dict[str, Any]:
    from .taste_profile import load_taste, save_taste

    taste = load_taste(root)

    def _dedupe(items: list[Any], *, limit: int) -> list[str]:
        out: list[str] = []
        for raw in items or []:
            t = str(raw or "").strip()
            if not t:
                continue
            low = t.lower()
            # Drop if contained in / contains an existing longer/shorter near-duplicate.
            drop = False
            replace_at = -1
            for i, prev in enumerate(out):
                pl = prev.lower()
                if low == pl:
                    drop = True
                    break
                if low in pl and len(t) < len(prev):
                    drop = True
                    break
                if pl in low and len(t) > len(prev):
                    replace_at = i
                    break
            if drop:
                continue
            if replace_at >= 0:
                out[replace_at] = t
            else:
                out.append(t)
        return out[-limit:]

    before = {
        "reject": len(taste.get("reject_phrases") or []),
        "style": len(taste.get("style_notes") or []),
        "banned": len(taste.get("banned_habits") or []),
        "keep": len(taste.get("keep_phrases") or []),
    }
    taste["reject_phrases"] = _dedupe(taste.get("reject_phrases") or [], limit=24)
    taste["style_notes"] = _dedupe(taste.get("style_notes") or [], limit=20)
    taste["banned_habits"] = _dedupe(taste.get("banned_habits") or [], limit=24)
    taste["keep_phrases"] = _dedupe(taste.get("keep_phrases") or [], limit=16)
    save_taste(root, taste)
    after = {
        "reject": len(taste.get("reject_phrases") or []),
        "style": len(taste.get("style_notes") or []),
        "banned": len(taste.get("banned_habits") or []),
        "keep": len(taste.get("keep_phrases") or []),
    }
    return {"before": before, "after": after}


def archive_old_converge_reports(root: Path, *, keep: int = 40) -> dict[str, Any]:
    conv = root / MEMORY_DIR / "converge"
    if not conv.is_dir():
        return {"moved": 0, "kept": 0}
    reports = sorted(conv.glob("*_report.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    keep_set = set(reports[:keep])
    arch = conv / "archive"
    arch.mkdir(parents=True, exist_ok=True)
    moved = 0
    for p in reports:
        if p in keep_set:
            continue
        dest = arch / p.name
        if dest.exists():
            dest = arch / f"{p.stem}_{int(p.stat().st_mtime)}{p.suffix}"
        shutil.move(str(p), str(dest))
        moved += 1
    return {"moved": moved, "kept": len(keep_set), "archive": arch.relative_to(root).as_posix()}


def run_hygiene(root: Path, data: dict[str, Any], *, apply: bool = True, accept_learn: bool = False) -> dict[str, Any]:
    """One-shot hygiene for doctor noise + disk taste/specs/archive."""
    report: dict[str, Any] = {"ran_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"), "apply": apply}

    report["candidates"] = prune_noise_candidates(root) if apply else {
        "dry_run": True,
        "noise": sum(
            1
            for c in __import__("lifecycle", fromlist=["load_candidates_file"]).load_candidates_file(root)
            if is_noise_candidate(str(c.get("module_id") or ""), str(c.get("folder") or ""))
        ),
    }
    report["detach"] = detach_missing_assets(root, apply=apply)
    if apply:
        report["specs"] = ensure_short_specs(root, data)
        report["taste"] = dedupe_taste_phrases(root)
        report["reports"] = archive_old_converge_reports(root, keep=40)
        if accept_learn:
            try:
                from .knowledge import cmd_learn

                rc = cmd_learn(
                    root,
                    data,
                    "accept",
                    accept_all=True,
                    seed_modules=False,
                    silent=False,
                    stash_only=True,
                )
                report["learn"] = {"ok": rc == 0, "rc": rc, "mode": "stash_only"}
            except Exception as exc:  # noqa: BLE001
                report["learn"] = {"ok": False, "error": str(exc)}
        else:
            report["learn"] = {"skipped": True, "reason": "default; pass accept_learn or --accept-learn"}
    elif not apply:
        report["learn"] = {"skipped": True, "reason": "dry-run"}
    return report


def print_hygiene_report(report: dict[str, Any]) -> None:
    print("🧹 pmem-art memory hygiene")
    print(f"   · 时间: {report.get('ran_at')}  apply={report.get('apply')}")
    cand = report.get("candidates") or {}
    if "before" in cand:
        print(f"   · candidates: {cand.get('before')} → {cand.get('after')}（丢弃噪声 {len(cand.get('dropped') or [])}）")
    else:
        print(f"   · candidates dry-run noise≈{cand.get('noise')}")
    det = report.get("detach") or {}
    print(f"   · detach: 改写条目 {det.get('touched', 0)} · 断链 {det.get('detached_links', 0)}")
    specs = report.get("specs") or {}
    if specs:
        print(f"   · specs: 新建 {len(specs.get('created') or [])} → {', '.join((specs.get('created') or [])[:8]) or '（无）'}")
    taste = report.get("taste") or {}
    if taste:
        b, a = taste.get("before") or {}, taste.get("after") or {}
        print(
            f"   · taste 去重: reject {b.get('reject')}→{a.get('reject')} · "
            f"style {b.get('style')}→{a.get('style')} · banned {b.get('banned')}→{a.get('banned')}"
        )
    rep = report.get("reports") or {}
    if rep:
        moved = int(rep.get("moved") or 0)
        arch = rep.get("archive") or ""
        print(
            f"   · converge reports: 保留 {rep.get('kept')} · 归档 {moved} → {arch}"
            + ("（可逆：从 archive 移回即可；Git 可能显示原路径 deleted）" if moved else "")
        )
    learn = report.get("learn")
    if learn is not None:
        if learn.get("skipped"):
            reason = str(learn.get("reason") or "")
            if reason == "dry-run":
                print("   · learn：dry-run 未改盘（apply 时默认不收；--accept-learn 仅消费队列）")
            else:
                print("   · learn：未收下提案（默认；显式 --accept-learn 才 learn accept --all，且仅消费队列）")
        else:
            print(f"   · learn accept: {learn}")
