#!/usr/bin/env python3
"""Build a user-facing pmem-art zip that does not include mry-ship/pmem."""
from __future__ import annotations

import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pmem_art import VERSION  # noqa: E402

PMEM_BEGIN = re.compile(r"\n*<!-- pmem:begin -->.*?<!-- pmem:end -->\s*", re.S)
PMEM_SKILL_DIRS = {
    "pmem-bootstrap",
    "pmem-compact",
    "pmem-consolidate",
    "pmem-normalize",
    "pmem-seed",
    "pmem-spec",
}
SKIP_DIR_NAMES = {
    ".git",
    ".memory",
    ".local",
    ".cache",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".memory-art",
    "generated_v8_20",
    "generated_v8_20_v2",
    "generated_v8_20_skill",
    "generated_v8_20_skill_grok",
    "generated_v8_20_skill_v2fix",
    "generated_v8_20_skill_look",
    "generated_v8_20_skill_opt1027",
    "reference_fresh",
    "images",
    "_box_sync",
    "_sync_parts",
}
SKIP_FILE_NAMES = {
    ".mcp.json",
    "pmem.mdc",
    "memory_write.lock",
    "apikey_fan.env",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".env"}
TMP_PREFIXES = ("_tmp_", "_probe_")


def _is_pmem_command(command: str) -> bool:
    text = " ".join(str(command or "").replace("\\", "/").split())
    if not text:
        return False
    if text == "pmem" or text.startswith("pmem "):
        return True
    if "pmem hook" in text or text.startswith("pmem hook"):
        return True
    if ".memory/bin/pmem-hook" in text:
        return True
    return False


def _walk_drop_pmem_hooks(node: Any) -> Any:
    if isinstance(node, dict):
        command = node.get("command")
        if isinstance(command, str) and _is_pmem_command(command):
            return None
        out: dict[str, Any] = {}
        for key, value in node.items():
            cleaned = _walk_drop_pmem_hooks(value)
            if cleaned is None:
                continue
            if key == "mcpServers" and isinstance(cleaned, dict):
                cleaned = {k: v for k, v in cleaned.items() if k != "pmem"}
            out[key] = cleaned
        return out
    if isinstance(node, list):
        cleaned_list = []
        for item in node:
            cleaned = _walk_drop_pmem_hooks(item)
            if cleaned is None:
                continue
            cleaned_list.append(cleaned)
        return cleaned_list
    return node


def sanitize_text(path: Path, text: str) -> str:
    name = path.name.replace("\\", "/")
    rel = str(path).replace("\\", "/")
    if name in {"AGENTS.md", "CLAUDE.md"} or rel.endswith("/AGENTS.md") or rel.endswith("/CLAUDE.md"):
        text = PMEM_BEGIN.sub("\n", text).rstrip() + "\n"
    if path.suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text
        cleaned = _walk_drop_pmem_hooks(data)
        if isinstance(cleaned, dict) and "mcpServers" in cleaned:
            servers = cleaned.get("mcpServers") or {}
            if isinstance(servers, dict):
                cleaned["mcpServers"] = {k: v for k, v in servers.items() if k != "pmem"}
        text = json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n"
    return text


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts
    if any(part in SKIP_DIR_NAMES for part in parts):
        return True
    if any(part in PMEM_SKILL_DIRS for part in parts):
        return True
    if path.name in SKIP_FILE_NAMES:
        return True
    if path.parent.name == "rules" and path.name == "pmem.mdc":
        return True
    if path.parent.name == ".codex" and path.name == "config.toml":
        return True
    if path.parent.name == ".claude" and path.name == "settings.json":
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    if path.name.startswith(TMP_PREFIXES):
        return True
    if path.name.endswith(".local.yaml"):
        return True
    return False


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path, root):
            continue
        files.append(path)
    return files


def pack(root: Path, dest_dir: Path | None = None) -> Path:
    dest_dir = dest_dir or (root / "dist")
    dest_dir.mkdir(parents=True, exist_ok=True)
    ver = str(VERSION).replace(" ", "")
    zip_path = dest_dir / f"pmem-art-{ver}.zip"
    if zip_path.exists():
        zip_path.unlink()
    prefix = f"pmem-art-{ver}"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src in iter_source_files(root):
            rel = src.relative_to(root).as_posix()
            arc = f"{prefix}/{rel}"
            if src.suffix.lower() in {".md", ".json", ".toml", ".mdc"} or src.name in {
                "AGENTS.md",
                "CLAUDE.md",
                "hooks.json",
                "mcp.json",
                "settings.json",
                "config.toml",
            }:
                try:
                    text = src.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    zf.write(src, arc)
                else:
                    zf.writestr(arc, sanitize_text(src, text))
            else:
                zf.write(src, arc)
    return zip_path


def assert_pack_clean(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        original = zf.namelist()
        names = [n.replace("\\", "/") for n in original]
        if any("/.memory/" in n or n.endswith("/.memory") for n in names):
            raise SystemExit("pack leaked .memory/")
        if any(part in PMEM_SKILL_DIRS for n in names for part in n.split("/")):
            raise SystemExit("pack leaked pmem R&D skills")
        if any(n.endswith(".mcp.json") or n.endswith("pmem.mdc") for n in names):
            raise SystemExit("pack leaked pmem mcp/rule files")
        for orig, name in zip(original, names):
            if name.endswith(("hooks.json", "mcp.json", "settings.json")):
                raw = zf.read(orig).decode("utf-8")
                if name.endswith("mcp.json"):
                    data = json.loads(raw)
                    servers = (data.get("mcpServers") or {}) if isinstance(data, dict) else {}
                    if "pmem" in servers:
                        raise SystemExit(f"pack leaked pmem MCP in {name}")
                if "pmem hook" in raw or ".memory/bin/pmem-hook" in raw:
                    raise SystemExit(f"pack leaked pmem hook in {name}")
            if name.endswith(("AGENTS.md", "CLAUDE.md")):
                raw = zf.read(orig).decode("utf-8")
                if "pmem:begin" in raw or "search_memory(" in raw:
                    raise SystemExit(f"pack leaked pmem agent block in {name}")


def main() -> int:
    zip_path = pack(ROOT)
    assert_pack_clean(zip_path)
    print(f"packed {zip_path} ({zip_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
