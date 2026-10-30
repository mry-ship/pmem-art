#!/usr/bin/env python3
"""Local reveal bridge for art-atlas: open Finder/Explorer and select a file.

Browsers cannot run `open -R` from file:// pages. This tiny localhost server
is started by `pmem_art.py atlas` so the workbench can call /api/reveal.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_PORT = 8765


def _cors(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


def _safe_under_root(root: Path, rel_or_abs: str) -> Path | None:
    raw = (rel_or_abs or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = (root / raw).resolve()
    else:
        p = p.expanduser().resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return None
    return p if p.exists() else None


def reveal_path(path: Path) -> bool:
    target = path.expanduser().resolve()
    if not target.exists():
        return False
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(target)], check=False)
        elif sys.platform == "win32":
            # 两段参数：explorer 会拼成 /select,<path>，路径带空格也能选中
            subprocess.Popen(["explorer", "/select,", str(target)])
        else:
            subprocess.run(["xdg-open", str(target.parent)], check=False)
        return True
    except OSError:
        return False


class RevealHandler(BaseHTTPRequestHandler):
    root: Path = Path(".").resolve()

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        return

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        _cors(self)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        _cors(self)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/api/ping", "/ping"):
            self._json(200, {"ok": True, "root": str(self.root), "pid": os.getpid()})
            return
        if parsed.path in ("/api/reveal", "/reveal"):
            qs = urllib.parse.parse_qs(parsed.query)
            target = _safe_under_root(self.root, (qs.get("path") or [""])[0])
            if not target:
                self._json(404, {"ok": False, "error": "not found"})
                return
            ok = reveal_path(target)
            self._json(200 if ok else 500, {"ok": ok, "path": str(target)})
            return
        self._json(404, {"ok": False, "error": "unknown"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/api/reveal", "/reveal"):
            self._json(404, {"ok": False})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        target = _safe_under_root(self.root, str(payload.get("path") or ""))
        if not target:
            self._json(404, {"ok": False})
            return
        ok = reveal_path(target)
        self._json(200 if ok else 500, {"ok": ok, "path": str(target)})


def run_server(root: Path, port: int = DEFAULT_PORT) -> None:
    RevealHandler.root = root.resolve()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), RevealHandler)
    httpd.serve_forever()


def ping_server(port: int = DEFAULT_PORT, timeout: float = 0.4) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=timeout) as resp:
            return int(getattr(resp, "status", 200) or 200) == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _port_free(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def write_port_files(root: Path, port: int, pid: int | None = None) -> None:
    mem = root / ".memory-art"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "atlas_reveal.port").write_text(str(port), encoding="utf-8")
    if pid is not None:
        (mem / "atlas_reveal.pid").write_text(str(pid), encoding="utf-8")


def ensure_reveal_daemon(root: Path, port: int = DEFAULT_PORT) -> int:
    """Ensure localhost reveal bridge is up; return port (0 if failed)."""
    root = root.resolve()
    for candidate in range(port, port + 12):
        if ping_server(candidate):
            write_port_files(root, candidate)
            return candidate

    chosen = None
    for candidate in range(port, port + 12):
        if _port_free(candidate):
            chosen = candidate
            break
    if chosen is None:
        return 0

    # Prefer running the module file so imports resolve from project root.
    cmd = [
        sys.executable,
        str((root / "atlas_reveal.py").resolve()),
        str(root),
        str(chosen),
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return 0
    write_port_files(root, chosen, proc.pid)
    for _ in range(40):
        time.sleep(0.05)
        if ping_server(chosen):
            return chosen
    return chosen if ping_server(chosen, timeout=1.0) else 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    port = int(argv[1]) if len(argv) > 1 else DEFAULT_PORT
    write_port_files(root, port, os.getpid())
    run_server(root, port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
