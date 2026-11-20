"""Art-memory trust tiers: candidate → verified → canonical (+ revoke / resolve)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

TRUST_LEVELS = ("candidate", "verified", "canonical")
TRUST_RANK = {"candidate": 0, "verified": 1, "canonical": 2}
_DEAD_STATUS = frozenset({"archived", "superseded", "inactive", "pending", "revoked"})


def normalize_trust(raw: object, *, status: object = "active") -> str:
    t = str(raw or "").strip().lower()
    if t in TRUST_LEVELS:
        return t
    st = str(status or "active").strip().lower()
    if st == "provisional" or st in _DEAD_STATUS:
        return "candidate"
    # Grandfather: legacy live entries without trust act as verified.
    return "verified"


def entry_trust(entry: dict[str, Any]) -> str:
    return normalize_trust(entry.get("trust"), status=entry.get("status"))


def trust_counts_for_recipe_confidence(entry: dict[str, Any]) -> bool:
    """Only verified/canonical recipes boost Warm-Start settle confidence."""
    if str(entry.get("kind") or "") != "recipe":
        return False
    st = str(entry.get("status") or "active").lower()
    if st in _DEAD_STATUS or st == "provisional":
        return False
    return entry_trust(entry) in ("verified", "canonical")


def trust_rank_tuple(entry: dict[str, Any]) -> int:
    return TRUST_RANK.get(entry_trust(entry), 0)


def _split_frontmatter(raw: str) -> tuple[str, str] | None:
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", raw, re.DOTALL)
    if not m:
        return None
    return m.group(1), m.group(2)


def _project_root_from_entry(path: Path) -> Path:
    for p in path.parents:
        if (p / ".memory-art").is_dir():
            return p
        if p.name == ".memory-art":
            return p.parent
    return path.parent


def _find_entry_file(root: Path, entry_id: str) -> Path | None:
    from lifecycle import iter_md_files

    needle = str(entry_id).strip()
    if not needle:
        return None
    entries_root = root / ".memory-art" / "entries"
    if not entries_root.is_dir():
        return None
    for md in iter_md_files(entries_root, recursive=True):
        if md.stem == needle:
            return md
        try:
            head = md.read_text(encoding="utf-8")[:400]
        except (OSError, UnicodeDecodeError):
            continue
        if re.search(rf"^id:\s*{re.escape(needle)}\s*$", head, re.M):
            return md
    return None


def _patch_frontmatter(path: Path, updates: dict[str, str]) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    parts = _split_frontmatter(raw)
    if parts is None:
        raise ValueError(f"not a memory entry markdown: {path}")
    fm, body = parts
    lines = fm.splitlines()
    keys_done: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        m = re.match(r"^([A-Za-z0-9_]+)\s*:", line)
        if m and m.group(1) in updates:
            key = m.group(1)
            new_lines.append(f"{key}: {updates[key]}")
            keys_done.add(key)
        else:
            new_lines.append(line)
    for key, val in updates.items():
        if key in keys_done:
            continue
        if key == "trust":
            inserted = False
            out: list[str] = []
            for ln in new_lines:
                out.append(ln)
                if re.match(r"^status\s*:", ln) and not inserted:
                    out.append(f"trust: {val}")
                    inserted = True
            new_lines = out if inserted else (new_lines + [f"trust: {val}"])
        else:
            new_lines.append(f"{key}: {val}")
    new_raw = "---\n" + "\n".join(new_lines) + "\n---\n" + (body if body.endswith("\n") else body + "\n")
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(new_raw, encoding="utf-8")
    tmp.replace(path)
    try:
        from improve import sync_active_project_to_library

        sync_active_project_to_library(_project_root_from_entry(path))
    except Exception:
        pass
    return {"path": str(path), "updates": updates}


def promote_entry(
    root: Path,
    entry_id: str,
    *,
    to: str,
    by: str = "",
) -> dict[str, Any]:
    target = str(to).strip().lower()
    if target not in TRUST_LEVELS:
        raise ValueError(f"trust must be one of {TRUST_LEVELS}")
    if target == "candidate":
        raise ValueError("use revoke or rewrite to demote; promote target is verified|canonical")
    path = _find_entry_file(root, entry_id)
    if path is None:
        raise FileNotFoundError(f"entry not found: {entry_id}")
    updates = {
        "trust": target,
        "status": "active",
    }
    if by:
        updates["trust_by"] = json_dumps_str(by)
    from datetime import datetime

    updates["trust_at"] = f"'{datetime.now().strftime('%Y-%m-%d')}'"
    result = _patch_frontmatter(path, updates)
    result["id"] = entry_id
    result["trust"] = target
    return result


def revoke_entry(root: Path, entry_id: str, *, reason: str = "") -> dict[str, Any]:
    path = _find_entry_file(root, entry_id)
    if path is None:
        raise FileNotFoundError(f"entry not found: {entry_id}")
    updates = {"status": "revoked", "trust": "candidate"}
    if reason:
        updates["revoke_reason"] = json_dumps_str(reason)
    result = _patch_frontmatter(path, updates)
    result["id"] = entry_id
    return result


def resolve_conflict(
    root: Path,
    *,
    keep_id: str,
    drop_id: str,
    reason: str = "",
) -> dict[str, Any]:
    keep_path = _find_entry_file(root, keep_id)
    drop_path = _find_entry_file(root, drop_id)
    if keep_path is None:
        raise FileNotFoundError(f"keep entry not found: {keep_id}")
    if drop_path is None:
        raise FileNotFoundError(f"drop entry not found: {drop_id}")
    keep_updates = {"status": "active"}
    # Prefer raising keep to at least verified if still candidate
    raw_keep = keep_path.read_text(encoding="utf-8")
    m = re.search(r"^trust:\s*(\w+)", raw_keep, re.M)
    cur = (m.group(1) if m else "").lower()
    if cur not in ("verified", "canonical"):
        keep_updates["trust"] = "verified"
    drop_updates = {"status": "superseded", "trust": "candidate"}
    if reason:
        drop_updates["superseded_by"] = keep_id
        drop_updates["supersede_reason"] = json_dumps_str(reason)
    k = _patch_frontmatter(keep_path, keep_updates)
    d = _patch_frontmatter(drop_path, drop_updates)
    return {"keep": k, "drop": d, "reason": reason}


def json_dumps_str(s: str) -> str:
    import json

    return json.dumps(s, ensure_ascii=False)


def _recipe_pass_score(meta: dict[str, Any]) -> float | None:
    """Best-effort score from ai_params / body for a recipe entry dict or frontmatter."""
    import json as _json

    params = meta.get("ai_params")
    if isinstance(params, str):
        try:
            params = _json.loads(params)
        except Exception:
            params = None
    if isinstance(params, dict) and params.get("score") is not None:
        try:
            return float(params.get("score"))
        except (TypeError, ValueError):
            pass
    if meta.get("score") is not None:
        try:
            return float(meta.get("score"))
        except (TypeError, ValueError):
            pass
    return None


def _load_module_recipe_metas(root: Path, module: str) -> list[dict[str, Any]]:
    from lifecycle import iter_md_files

    mod_dir = root / ".memory-art" / "entries" / module
    if not mod_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for md in iter_md_files(mod_dir, recursive=False):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        parts = _split_frontmatter(raw)
        if parts is None:
            continue
        fm, _body = parts
        try:
            from pmem_art import load_yaml

            meta = load_yaml(fm) or {}
        except Exception:
            continue
        if not isinstance(meta, dict):
            continue
        if str(meta.get("kind") or "") != "recipe":
            continue
        meta["_path"] = str(md)
        meta["_id"] = str(meta.get("id") or md.stem)
        out.append(meta)
    return out


def maybe_auto_verify_on_repeat_pass(
    root: Path,
    *,
    module: str,
    threshold: float = 9.5,
) -> list[str]:
    """If the same module has ≥2 live recipes that already passed the bar, promote candidates → verified.

    One ≥9.5 finish stays candidate. A second passing recipe in the same module is treated as
    repeat verification for all passing candidates in that module (not a jump to canonical).
    """
    if not module:
        return []
    recipes = _load_module_recipe_metas(root, module)
    passing: list[dict[str, Any]] = []
    for meta in recipes:
        st = str(meta.get("status") or "active").lower()
        if st in _DEAD_STATUS or st == "provisional":
            continue
        score = _recipe_pass_score(meta)
        # Only explicit scored recipes count — unscored legacy actives must not mass-promote.
        if score is None:
            continue
        if float(score) + 1e-9 >= float(threshold):
            passing.append(meta)
    if len(passing) < 2:
        return []
    promoted: list[str] = []
    for meta in passing:
        if entry_trust(meta) != "candidate":
            continue
        eid = str(meta.get("_id") or meta.get("id") or "")
        if not eid:
            continue
        try:
            promote_entry(root, eid, to="verified", by="auto:repeat_pass")
            promoted.append(eid)
        except (ValueError, FileNotFoundError):
            continue
    return promoted


def cmd_memory_trust(root: Path, args: Any) -> int:
    action = str(getattr(args, "memory_action", "") or getattr(args, "action", "") or "")
    try:
        if action == "promote":
            eid = str(getattr(args, "id", "") or "").strip()
            to = str(getattr(args, "to", "") or "").strip()
            if not eid or not to:
                print("❌ memory promote 需要 --id 与 --to verified|canonical")
                return 2
            info = promote_entry(
                root,
                eid,
                to=to,
                by=str(getattr(args, "by", "") or ""),
            )
            print(f"✅ promoted {info['id']} → trust={info['trust']}")
            return 0
        if action == "revoke":
            info = revoke_entry(root, str(args.id), reason=str(getattr(args, "reason", "") or ""))
            print(f"✅ revoked {info['id']}")
            return 0
        if action == "resolve":
            info = resolve_conflict(
                root,
                keep_id=str(args.keep),
                drop_id=str(args.drop),
                reason=str(getattr(args, "reason", "") or ""),
            )
            print(f"✅ keep={args.keep} drop={args.drop} superseded")
            return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"❌ {exc}")
        return 2
    print("usage: memory promote|revoke|resolve …")
    return 2
