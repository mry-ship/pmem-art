"""Named call-points between modules that must not import each other.

A module that needs a service owned by another domain calls ``call("<name>", ...)``.
The implementation is attached by ``connectors.wiring.install()`` at the entry point.
With no handler attached, ``call`` is a no-op returning ``default``.
"""
from __future__ import annotations

from typing import Any, Callable

_HANDLERS: dict[str, Callable[..., Any]] = {}


def register(name: str, handler: Callable[..., Any]) -> None:
    """Attach (or replace) the handler for ``name``."""
    _HANDLERS[name] = handler


def unregister(name: str) -> None:
    _HANDLERS.pop(name, None)


def has(name: str) -> bool:
    return name in _HANDLERS


_WIRING_MODULE = "connectors.wiring"
_bootstrapped = False


def _bootstrap() -> None:
    """Load the connector layer once, so callers outside the CLI entry still get handlers.

    The module name is a string on purpose: core must not import upward.
    """
    global _bootstrapped
    if _bootstrapped:
        return
    _bootstrapped = True
    try:
        import importlib

        importlib.import_module(_WIRING_MODULE).install()
    except Exception:
        pass


def call(name: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    handler = _HANDLERS.get(name)
    if handler is None:
        _bootstrap()
        handler = _HANDLERS.get(name)
    if handler is None:
        return default
    return handler(*args, **kwargs)
