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
    # 没写 trust 不再当成已验证。doctor 堆积仍只数显式 trust=candidate，避免把整库旧条目塞进 promote 队列。
    return "candidate"


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


def maybe_auto_verify_on_repeat_pass(
    root: Path,
    *,
    module: str,
    threshold: float = 9.5,
) -> list[str]:
    """自评达标不升级。verified 只来自人工 `memory promote`。

    签名保留给 converge finish。同模块多次 ≥ 阈值不再把 candidate 升成 verified。
    """
    del root, module, threshold
    return []


_INJECT_KINDS = frozenset({"style_redline", "art_decision", "recipe"})
_DEFAULT_PROMOTE_MISSING_KINDS = frozenset({"style_redline", "art_decision"})


def _entry_live_for_trust(entry: dict[str, Any]) -> bool:
    st = str(entry.get("status") or "active").strip().lower()
    return st not in _DEAD_STATUS and st != "provisional"


def _load_library_entries(root: Path) -> list[dict[str, Any]]:
    """Best-effort load of live art-memory entry dicts for audit/migrate."""
    from lifecycle import iter_md_files

    entries_root = root / ".memory-art" / "entries"
    if not entries_root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for md in iter_md_files(entries_root, recursive=True):
        try:
            raw = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        parts = _split_frontmatter(raw)
        if parts is None:
            continue
        fm, _body = parts
        meta: dict[str, Any] = {}
        for line in fm.splitlines():
            m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip()
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            meta[key] = val
        if not meta.get("id"):
            meta["id"] = md.stem
        meta["_path"] = str(md)
        out.append(meta)
    return out


def audit_trust_entries(
    root: Path,
    *,
    module: str = "",
    kinds: frozenset[str] | set[str] | None = None,
) -> dict[str, Any]:
    """Count live entries that cannot inject (missing trust or still candidate)."""
    want_kinds = frozenset(kinds) if kinds else _INJECT_KINDS
    mod = str(module or "").strip()
    missing: list[dict[str, str]] = []
    candidates: list[dict[str, str]] = []
    verified = 0
    for entry in _load_library_entries(root):
        kind = str(entry.get("kind") or "")
        if kind not in want_kinds:
            continue
        if not _entry_live_for_trust(entry):
            continue
        em = str(entry.get("module") or "")
        if mod and em != mod and not em.startswith(mod + "."):
            continue
        raw_trust = str(entry.get("trust") or "").strip().lower()
        row = {
            "id": str(entry.get("id") or ""),
            "kind": kind,
            "module": em,
            "summary": str(entry.get("summary") or "")[:80],
        }
        if not raw_trust:
            missing.append(row)
            continue
        if raw_trust == "candidate":
            candidates.append(row)
            continue
        if raw_trust in ("verified", "canonical"):
            verified += 1
    return {
        "missing_trust": missing,
        "explicit_candidate": candidates,
        "verified_or_canonical": verified,
        "missing_total": len(missing),
        "candidate_total": len(candidates),
    }


def promote_missing_trust(
    root: Path,
    *,
    to: str = "verified",
    by: str = "",
    module: str = "",
    kinds: frozenset[str] | set[str] | None = None,
    apply: bool = False,
    limit: int = 0,
) -> dict[str, Any]:
    """Promote live entries that lack a trust field (upgrade migration helper).

    Default kinds are style_redline + art_decision (injectable). Recipes are
    opt-in via --kind recipe. Dry-run unless apply=True.
    """
    target = str(to or "verified").strip().lower()
    if target not in ("verified", "canonical"):
        raise ValueError("promote-missing --to must be verified|canonical")
    want_kinds = frozenset(kinds) if kinds else _DEFAULT_PROMOTE_MISSING_KINDS
    audit = audit_trust_entries(root, module=module, kinds=want_kinds)
    rows = list(audit["missing_trust"])
    if limit and limit > 0:
        rows = rows[: int(limit)]
    promoted: list[str] = []
    if apply:
        for row in rows:
            eid = row["id"]
            if not eid:
                continue
            promote_entry(root, eid, to=target, by=by or "promote-missing")
            promoted.append(eid)
    return {
        "apply": bool(apply),
        "to": target,
        "kinds": sorted(want_kinds),
        "planned": rows,
        "planned_total": len(rows),
        "promoted": promoted,
        "promoted_total": len(promoted),
    }


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
        if action == "audit":
            kind_raw = str(getattr(args, "kind", "") or "").strip()
            kinds = (
                frozenset(x.strip() for x in kind_raw.split(",") if x.strip())
                if kind_raw
                else None
            )
            report = audit_trust_entries(
                root,
                module=str(getattr(args, "module", "") or ""),
                kinds=kinds,
            )
            print(
                "📋 memory audit（live · 可注入种类）\n"
                f"   缺 trust（不进提示词）: {report['missing_total']}\n"
                f"   显式 candidate（不进提示词）: {report['candidate_total']}\n"
                f"   verified/canonical: {report['verified_or_canonical']}"
            )
            for label, key in (
                ("缺 trust 样本", "missing_trust"),
                ("candidate 样本", "explicit_candidate"),
            ):
                rows = report.get(key) or []
                if not rows:
                    continue
                print(f"\n   {label}:")
                for row in rows[:12]:
                    print(
                        f"      - [{row.get('kind')}] {row.get('id')} "
                        f"@{row.get('module')} · {row.get('summary')}"
                    )
            if report["missing_total"]:
                print(
                    "\n   迁移预览: memory promote-missing --to verified --by \"…\""
                    "\n   确认写入: memory promote-missing --to verified --by \"…\" --apply"
                )
            return 0
        if action == "promote-missing":
            to = str(getattr(args, "to", "") or "verified").strip() or "verified"
            kind_raw = str(getattr(args, "kind", "") or "").strip()
            kinds = (
                frozenset(x.strip() for x in kind_raw.split(",") if x.strip())
                if kind_raw
                else None
            )
            limit = int(getattr(args, "limit", 0) or 0)
            apply = bool(getattr(args, "apply", False))
            result = promote_missing_trust(
                root,
                to=to,
                by=str(getattr(args, "by", "") or ""),
                module=str(getattr(args, "module", "") or ""),
                kinds=kinds,
                apply=apply,
                limit=limit,
            )
            mode = "已写入" if apply else "预览（未写盘，加 --apply 才升级）"
            print(
                f"{'✅' if apply else '👀'} promote-missing → trust={result['to']} · {mode}\n"
                f"   kinds={','.join(result['kinds'])}  planned={result['planned_total']}  "
                f"promoted={result['promoted_total']}"
            )
            for row in (result.get("planned") or [])[:15]:
                mark = "→" if apply else "·"
                print(
                    f"   {mark} [{row.get('kind')}] {row.get('id')} @{row.get('module')}"
                )
            if not apply and result["planned_total"]:
                print("   确认无误后再加 --apply。")
            return 0
    except (ValueError, FileNotFoundError) as exc:
        print(f"❌ {exc}")
        return 2
    print("usage: memory promote|revoke|resolve|audit|promote-missing …")
    return 2
