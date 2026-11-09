"""Background / alpha policy by image engine.

Cursor GenerateImage cannot emit true transparency. Prefer opaque isolation
backgrounds there; never chroma-key after the fact. Engines that support alpha
(e.g. gpt-image) may request true transparent PNGs directly.
"""
from __future__ import annotations

from typing import Any

# Default path in this repo is Cursor GenerateImage.
DEFAULT_ENGINE = "cursor.GenerateImage"

# Engines known to emit usable alpha when asked.
ALPHA_CAPABLE_ENGINES = frozenset(
    {
        "gpt-image",
        "gpt-image-1",
        "gpt-image-1.5",
        "gpt-image-2",
        "gpt-image-2.5",
        "openai.images",
        "openai_images",
        "apikey.fan",
        "apikey-image",
    }
)

# Engines that must stay opaque (no alpha channel in output).
OPAQUE_ONLY_ENGINES = frozenset(
    {
        "cursor",
        "cursor.generateimage",
        "cursor.GenerateImage",
        "generateimage",
    }
)

ISOLATION_BG_DEFAULT = "pure_black"
ISOLATION_BG_HEX = "#000000"


def normalize_engine(engine: str | None) -> str:
    raw = (engine or "").strip()
    return raw or DEFAULT_ENGINE


def _engine_key(engine: str | None) -> str:
    return normalize_engine(engine).strip().lower().replace(" ", "")


def engine_supports_alpha(engine: str | None) -> bool:
    """True only when the engine can natively emit transparent PNGs."""
    key = _engine_key(engine)
    if key in {e.lower().replace(" ", "") for e in OPAQUE_ONLY_ENGINES}:
        return False
    if key in {e.lower().replace(" ", "") for e in ALPHA_CAPABLE_ENGINES}:
        return True
    # Unknown third-party: do not assume alpha; prefer opaque isolation.
    return False


def post_key_allowed(engine: str | None = None) -> bool:
    """Post-hoc chroma-key / corner dig to fake alpha is never the default path."""
    del engine  # capability does not authorize keying; providers that support alpha should emit it.
    return False


def isolation_mode(engine: str | None = None, *, want_transparent: bool = True) -> str:
    """
    Return delivery mode for 「要透明底」briefs:
    - ``true_alpha``: native transparent PNG
    - ``opaque_isolation``: solid empty bg (default pure black)
    """
    if want_transparent and engine_supports_alpha(engine):
        return "true_alpha"
    return "opaque_isolation"


def bg_prompt_clause(
    engine: str | None = None,
    *,
    want_transparent: bool = True,
    solid_hex: str = ISOLATION_BG_HEX,
) -> str:
    """One short Chinese+EN clause to drop into revised prompts."""
    mode = isolation_mode(engine, want_transparent=want_transparent)
    if mode == "true_alpha":
        return "真 alpha 透明底 transparent PNG background, corners fully transparent, no white/magenta card"
    hex_v = (solid_hex or ISOLATION_BG_HEX).strip() or ISOLATION_BG_HEX
    return (
        f"不透明隔离底 flat solid {hex_v} background, empty stage, no scene, no white card; "
        "本引擎无透明通道，禁止成图后再抠色冒充 alpha"
    )


def judge_alpha_label(engine: str | None = None) -> str:
    """Display name for the icon-C / UI isolation dimension."""
    if engine_supports_alpha(engine):
        return "透明底"
    return "底隔离"


def policy_summary(engine: str | None = None) -> dict[str, Any]:
    eng = normalize_engine(engine)
    supports = engine_supports_alpha(eng)
    return {
        "engine": eng,
        "supports_alpha": supports,
        "post_key_allowed": False,
        "isolation_mode": isolation_mode(eng),
        "default_solid_hex": ISOLATION_BG_HEX,
        "bg_clause": bg_prompt_clause(eng),
        "judge_dim_label": judge_alpha_label(eng),
    }
