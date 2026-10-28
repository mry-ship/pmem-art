"""Multi-project library binding for pmem-art."""
from __future__ import annotations

import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

PROFILE_DIR = "_profile"
REFLECTIONS_DIR = "_reflections"
TASTE_FILE = "taste.json"
PROJECTS_DIR = "projects"
ACTIVE_PROJECT_FILE = "active_project.json"


def slugify_project_id(name: str) -> str:
    """Normalize a project name or directory basename into a stable project_id slug."""
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", (name or "").strip().lower(), flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "default_project"


def active_project_meta_path(root: Path) -> Path:
    return root / ".memory-art" / ACTIVE_PROJECT_FILE


def projects_root_dir(root: Path) -> Path:
    d = root / ".memory-art" / PROJECTS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def project_library_dir(root: Path, project_id: str) -> Path:
    return projects_root_dir(root) / slugify_project_id(project_id)


def _read_project_name_from_config(mem_dir: Path, fallback: str) -> str:
    cfg_file = mem_dir / "config.yaml"
    if cfg_file.is_file():
        try:
            raw = cfg_file.read_text(encoding="utf-8")
            m = re.search(r"^\s*name:\s*(.+?)\s*$", raw, re.M)
            if m:
                val = m.group(1).strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if val and val != "Untitled Art Project":
                    return val
        except Exception:
            pass
    return fallback


def _count_md_entries(entries_dir: Path) -> int:
    if not entries_dir.is_dir():
        return 0
    from lifecycle import iter_md_files
    return sum(1 for _ in iter_md_files(entries_dir, recursive=True))


def _count_modules_in_yaml(mod_file: Path) -> int:
    if not mod_file.is_file():
        return 0
    try:
        raw = mod_file.read_text(encoding="utf-8")
        try:
            import yaml
            y = yaml.safe_load(raw) or {}
            return len((y.get("modules") or {}))
        except Exception:
            return len(re.findall(r"^\s{2}[a-zA-Z0-9_.]+:\s*$", raw, re.M))
    except Exception:
        return 0


def _snapshot_surface_to_library_dir(
    mem_dir: Path,
    lib_dir: Path,
    *,
    project_id: str,
    project_name: str,
    origin_root: str,
    created_at: str = "",
    copied_from_project: str = "",
    mirror_exact: bool = True,
) -> dict[str, Any]:
    """Copy the active working surface in `.memory-art/` into `.memory-art/projects/<project_id>/`
    and write `library.json` + `library_meta.json`.
    """
    lib_dir.mkdir(parents=True, exist_ok=True)
    now_str = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")

    # Preserve created_at if library.json already exists
    existing_meta: dict[str, Any] = {}
    for mf in ("library.json", "library_meta.json"):
        mp = lib_dir / mf
        if mp.is_file():
            try:
                existing_meta = json.loads(mp.read_text(encoding="utf-8"))
                break
            except Exception:
                pass
    created_ts = created_at or existing_meta.get("created_at") or now_str

    for fname in ("config.yaml", "modules.yaml", "candidates.json"):
        src = mem_dir / fname
        if src.is_file():
            shutil.copy2(src, lib_dir / fname)

    for dname in ("entries", "_profile", "_knowledge", "_reflections", "inbox"):
        src_d = mem_dir / dname
        dst_d = lib_dir / dname
        if src_d.is_dir():
            if mirror_exact and dst_d.is_dir():
                shutil.rmtree(dst_d)
            shutil.copytree(src_d, dst_d, dirs_exist_ok=True)
        else:
            dst_d.mkdir(parents=True, exist_ok=True)

    entry_cnt = _count_md_entries(lib_dir / "entries")
    mod_cnt = _count_modules_in_yaml(lib_dir / "modules.yaml")

    lib_meta = {
        "project_id": project_id,
        "project_slug": project_id,
        "project_name": project_name,
        "layer_scope": "private",
        "origin_root": origin_root,
        "origin_path": origin_root,
        "bound_root": origin_root,
        "root_fingerprint": origin_root,
        "entry_count": entry_cnt,
        "entries_count": entry_cnt,
        "modules_count": mod_cnt,
        "copied_from_project": copied_from_project or existing_meta.get("copied_from_project", ""),
        "created_at": created_ts,
        "updated_at": now_str,
    }
    payload = json.dumps(lib_meta, ensure_ascii=False, indent=2) + "\n"
    (lib_dir / "library.json").write_text(payload, encoding="utf-8")
    (lib_dir / "library_meta.json").write_text(payload, encoding="utf-8")
    return lib_meta


def sync_active_project_to_library(
    root: Path,
    *,
    project_name: str = "",
) -> dict[str, Any]:
    """Sync the current `.memory-art/` working surface into `.memory-art/projects/<active-project-slug>/`."""
    root = root.resolve()
    mem = root / ".memory-art"
    if not mem.is_dir():
        return {}
    meta = ensure_project_library_bound(root, explicit_project_name=project_name, _skip_sync=True)
    pid = meta.get("project_id") or slugify_project_id(root.name)
    pname = project_name or meta.get("project_name") or _read_project_name_from_config(mem, root.name)
    if project_name and project_name != meta.get("project_name"):
        meta["project_name"] = pname
        meta["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
        active_project_meta_path(root).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    lib_dir = project_library_dir(root, pid)
    _snapshot_surface_to_library_dir(
        mem,
        lib_dir,
        project_id=pid,
        project_name=pname,
        origin_root=str(root),
        created_at=meta.get("created_at", ""),
        copied_from_project=meta.get("copied_from_project", ""),
        mirror_exact=True,
    )
    return meta


def ensure_project_library_bound(
    root: Path,
    *,
    explicit_project_name: str = "",
    _skip_sync: bool = False,
) -> dict[str, Any]:
    """Ensure `.memory-art/` is bound to `root`.
    If `.memory-art/` was copied from a previous project (e.g., `bound_root != str(root.resolve())`
    or `project_id != slugify_project_id(root.name)`), automatically:
      1. Archive/preserve the previous project's specialized library intact under
         `.memory-art/projects/<prev_project_id>/`.
      2. Reset the active working surface in `.memory-art/` (`entries/`, `_profile/taste.json`,
         `_knowledge/`, `_reflections/`, `candidates.json`, `config.yaml`, `modules.yaml`)
         so the new project starts with a 100% clean private specialized library.
      3. Bind `.memory-art/active_project.json` and initialize `.memory-art/projects/<new_project_id>/`.
    """
    root = root.resolve()
    mem = root / ".memory-art"
    if not mem.is_dir():
        return {}

    now_str = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    curr_root_str = str(root)
    curr_id = slugify_project_id(root.name)
    active_file = active_project_meta_path(root)

    if not active_file.is_file():
        pname = explicit_project_name or _read_project_name_from_config(mem, root.name)
        meta = {
            "project_id": curr_id,
            "project_slug": curr_id,
            "project_name": pname,
            "layer_scope": "private",
            "bound_root": curr_root_str,
            "origin_root": curr_root_str,
            "root_name": root.name,
            "library_dir": f".memory-art/{PROJECTS_DIR}/{curr_id}",
            "copied_from_project": "",
            "created_at": now_str,
            "updated_at": now_str,
        }
        active_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not _skip_sync:
            _snapshot_surface_to_library_dir(
                mem,
                project_library_dir(root, curr_id),
                project_id=curr_id,
                project_name=pname,
                origin_root=curr_root_str,
                created_at=now_str,
                mirror_exact=True,
            )
        return meta

    try:
        active_meta = json.loads(active_file.read_text(encoding="utf-8"))
    except Exception:
        active_meta = {}

    prev_root = str(active_meta.get("bound_root") or "")
    prev_id = str(active_meta.get("project_id") or "")
    prev_name = str(active_meta.get("project_name") or prev_id or "Previous Project")

    is_copied_to_new_project = False
    if prev_id and prev_id != curr_id:
        is_copied_to_new_project = True
    elif prev_root and prev_root != curr_root_str:
        # Isolate even when the old absolute path is gone (folder moved/copied then deleted).
        # Only skip when old path still exists and resolves to the same directory (symlink/rename noop).
        try:
            prev_p = Path(prev_root)
            if prev_p.exists():
                if prev_p.resolve() != root.resolve():
                    is_copied_to_new_project = True
            else:
                is_copied_to_new_project = True
        except Exception:
            is_copied_to_new_project = True

    if is_copied_to_new_project:
        archive_id = prev_id or slugify_project_id(Path(prev_root).name if prev_root else "previous_project")
        archive_dir = project_library_dir(root, archive_id)
        print(
            "⚠️  [拷贝隔离] 检测到项目目录被复制/改名："
            f"旧 root={prev_root or prev_id!r} → 新 root={curr_root_str!r}。\n"
            f"   顶层 `.memory-art/entries` / taste / converge / _knowledge 将清空并重建脚手架；\n"
            f"   历史记忆已归档到 `.memory-art/projects/{archive_id}/`（不会删库，但工作面为空）。\n"
            "   若这是误触发：勿继续写记忆；把目录移回原路径或从 projects/ 拷回后再开 CLI。"
        )
        # 1. Preserve previous project's specialized library intact under .memory-art/projects/<archive_id>/
        _snapshot_surface_to_library_dir(
            mem,
            archive_dir,
            project_id=archive_id,
            project_name=prev_name,
            origin_root=prev_root or curr_root_str,
            created_at=str(active_meta.get("created_at") or now_str),
            mirror_exact=False,
        )

        # 2. Reset active working surface in .memory-art/ for the new project
        new_pname = explicit_project_name or root.name
        entries_d = mem / "entries"
        if entries_d.is_dir():
            shutil.rmtree(entries_d)
        entries_d.mkdir(parents=True, exist_ok=True)

        prof_d = mem / PROFILE_DIR
        if prof_d.is_dir():
            shutil.rmtree(prof_d)
        prof_d.mkdir(parents=True, exist_ok=True)
        clean_taste = json.loads(json.dumps(DEFAULT_TASTE))
        clean_taste["project_id"] = curr_id
        clean_taste["project_name"] = new_pname
        clean_taste["updated_at"] = now_str
        (prof_d / TASTE_FILE).write_text(
            json.dumps(clean_taste, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        know_d = mem / "_knowledge"
        if know_d.is_dir():
            shutil.rmtree(know_d)
        know_d.mkdir(parents=True, exist_ok=True)
        clean_kidx = {
            "version": 1,
            "layer_scope": "private",
            "project_id": curr_id,
            "project_name": new_pname,
            "cards": {},
            "updated_at": now_str,
        }
        (know_d / "index.json").write_text(
            json.dumps(clean_kidx, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        refl_d = mem / REFLECTIONS_DIR
        if refl_d.is_dir():
            shutil.rmtree(refl_d)
        refl_d.mkdir(parents=True, exist_ok=True)

        conv_d = mem / "converge"
        if conv_d.is_dir():
            shutil.rmtree(conv_d)

        inbox_d = mem / "inbox"
        if inbox_d.is_dir():
            shutil.rmtree(inbox_d)
        inbox_d.mkdir(parents=True, exist_ok=True)

        (mem / "candidates.json").write_text("[]\n", encoding="utf-8")

        try:
            from lifecycle import default_config, STARTER_CATEGORIES, STARTER_MODULES, write_config_yaml, write_modules_yaml
            write_config_yaml(root, default_config(project_name=new_pname, mode="young"))
            write_modules_yaml(root, STARTER_CATEGORIES, STARTER_MODULES)
        except Exception:
            pass

        new_meta = {
            "project_id": curr_id,
            "project_slug": curr_id,
            "project_name": new_pname,
            "layer_scope": "private",
            "bound_root": curr_root_str,
            "origin_root": curr_root_str,
            "root_name": root.name,
            "library_dir": f".memory-art/{PROJECTS_DIR}/{curr_id}",
            "copied_from_project": archive_id,
            "copied_from_root": prev_root,
            "auto_isolated_on_copy": True,
            "created_at": now_str,
            "updated_at": now_str,
        }
        active_file.write_text(json.dumps(new_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _snapshot_surface_to_library_dir(
            mem,
            project_library_dir(root, curr_id),
            project_id=curr_id,
            project_name=new_pname,
            origin_root=curr_root_str,
            created_at=now_str,
            copied_from_project=archive_id,
            mirror_exact=True,
        )
        return new_meta

    # Same root: update project_name if explicitly passed or changed in config.yaml
    cfg_pname = _read_project_name_from_config(mem, "")
    updated_name = explicit_project_name or (
        cfg_pname if cfg_pname and active_meta.get("project_name") in ("", root.name, "Untitled Art Project") else ""
    )
    if updated_name and updated_name != active_meta.get("project_name"):
        active_meta["project_name"] = updated_name
        active_meta["updated_at"] = now_str
        active_file.write_text(json.dumps(active_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    active_meta.setdefault("project_id", curr_id)
    active_meta.setdefault("project_slug", active_meta["project_id"])
    active_meta.setdefault("project_name", cfg_pname or root.name)
    active_meta.setdefault("layer_scope", "private")
    active_meta.setdefault("library_dir", f".memory-art/{PROJECTS_DIR}/{active_meta['project_id']}")

    if not _skip_sync and not project_library_dir(root, active_meta["project_id"]).is_dir():
        _snapshot_surface_to_library_dir(
            mem,
            project_library_dir(root, active_meta["project_id"]),
            project_id=active_meta["project_id"],
            project_name=active_meta["project_name"],
            origin_root=curr_root_str,
            created_at=str(active_meta.get("created_at") or now_str),
            copied_from_project=str(active_meta.get("copied_from_project") or ""),
            mirror_exact=True,
        )
    return active_meta

DEFAULT_TASTE: dict[str, Any] = {
    "version": 1,
    "updated_at": "",
    "preferred_lighting": [],
    "preferred_composition": [],
    "preferred_line_weight": [],
    "preferred_color_temperature": [],
    "banned_habits": [],
    "keep_phrases": [],
    "reject_phrases": [],
    "style_notes": [],
    "signal_counts": {
        "keeps": 0,
        "rejects": 0,
        "style_fixes": 0,
        "sessions": 0,
    },
}

