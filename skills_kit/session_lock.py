"""Per-session exclusive lock and revision conflict for converge JSON."""
from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    import fcntl as _fcntl

    _fcntl.LOCK_EX
    _fcntl.flock
except (ImportError, AttributeError):
    _fcntl = None

_LOCK_EX = getattr(_fcntl, "LOCK_EX", 2)
_LOCK_NB = getattr(_fcntl, "LOCK_NB", 4)
_LOCK_UN = getattr(_fcntl, "LOCK_UN", 8)
_held = threading.local()


class SessionRevisionConflict(RuntimeError):
    """A writer loaded an older revision than the file now on disk."""


def _flock(fd: int, flags: int) -> None:
    if _fcntl is not None:
        _fcntl.flock(fd, flags)
        return
    try:
        import msvcrt
    except ImportError:
        return
    os.lseek(fd, 0, os.SEEK_SET)
    if flags & _LOCK_UN:
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    if os.fstat(fd).st_size < 1:
        os.write(fd, b"\0")
        os.lseek(fd, 0, os.SEEK_SET)
    mode = msvcrt.LK_NBLCK if flags & _LOCK_NB else msvcrt.LK_LOCK
    try:
        msvcrt.locking(fd, mode, 1)
    except OSError:
        if flags & _LOCK_NB:
            raise BlockingIOError("session lock busy")
        raise


@contextmanager
def session_file_lock(sf: Path, *, timeout_sec: float = 30.0) -> Iterator[None]:
    """Cross-process lock for one session file. Re-entrant in the same thread."""
    key = str(Path(sf).resolve())
    held: set[str] | None = getattr(_held, "keys", None)
    if held is None:
        held = set()
        _held.keys = held
    if key in held:
        yield
        return
    lock_path = Path(sf).with_name(Path(sf).name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.time() + timeout_sec
    while True:
        try:
            _flock(fd, _LOCK_EX | _LOCK_NB)
            break
        except BlockingIOError:
            if time.time() >= deadline:
                os.close(fd)
                raise TimeoutError(f"会话锁忙: {lock_path.name}")
            time.sleep(0.02)
    held.add(key)
    try:
        yield
    finally:
        held.discard(key)
        try:
            _flock(fd, _LOCK_UN)
        finally:
            os.close(fd)
