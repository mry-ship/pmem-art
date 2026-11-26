"""The one place where cross-domain calls are wired to their implementations.

Domain modules call ``core.hooks.call(<name>)``. This module maps each name to
the real function. Imports of the target are deferred so that importing this
file stays cheap and cannot create import cycles.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core import hooks

ATLAS_REFRESH = "atlas.refresh"
PROJECT_LOAD = "project.load"
SKILLS_INSTALL = "skills.install"


def _atlas_refresh(root: Path, out_name: str = "art-atlas.html") -> Path | None:
    from pmem_art import refresh_atlas_silent

    return refresh_atlas_silent(root, out_name)


def _project_load(root: Path, *, embed_images: bool = False) -> dict[str, Any]:
    from pmem_art import load_project

    return load_project(root, embed_images=embed_images)


def _skills_install(root: Path, quiet: bool = False) -> Any:
    from skills_kit.install import install_skills_and_agent_configs

    return install_skills_and_agent_configs(root, quiet=quiet)


HANDLERS: dict[str, Any] = {
    ATLAS_REFRESH: _atlas_refresh,
    PROJECT_LOAD: _project_load,
    SKILLS_INSTALL: _skills_install,
}


def install() -> None:
    """Attach every handler. Idempotent; call once from an entry point."""
    for name, fn in HANDLERS.items():
        hooks.register(name, fn)
