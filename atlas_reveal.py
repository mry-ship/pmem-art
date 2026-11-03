#!/usr/bin/env python3
"""Local reveal/delete bridge for art-atlas: open Finder/Explorer and select a file.

Browsers cannot run `open -R` from file:// pages. This tiny localhost server
is started by `pmem_art.py atlas` so the workbench can call /api/reveal
and /api/delete.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# 避开本机常被占满的 8765 一带；旧版仍会回退探测
DEFAULT_PORT = 27865
SERVICE_NAME = "pmem-atlas-reveal"
TRASH_REL = ".memory-art/_trash"
# 教学示例图写死目录：工作台删除一律拒绝
PROTECTED_PREFIXES = (
    "docs/workbench_guide/",
    ".memory-art/_trash/",
)
IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".svg",
}


def _cors(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    # Chrome/Edge：file:// 或跨站访问本机环回时需要 Private Network Access 预检头
    handler.send_header("Access-Control-Allow-Private-Network", "true")


_STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
}

_STATIC_BLOCK_PREFIXES = (
    ".git/",
    ".env",
    "node_modules/",
)


def _safe_under_root(root: Path, rel_or_abs: str, *, must_exist: bool = True) -> Path | None:
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
    if must_exist and not p.exists():
        return None
    return p


def reveal_path(path: Path) -> bool:
    target = path.expanduser().resolve()
    if not target.exists():
        return False
    try:
        if sys.platform == "darwin":
            if target.is_dir():
                subprocess.run(["open", str(target)], check=False)
            else:
                subprocess.run(["open", "-R", str(target)], check=False)
        elif sys.platform == "win32":
            if target.is_dir():
                # 直接打开文件夹（垃圾桶 / 教学目录）
                subprocess.Popen(["explorer", str(target)])
            else:
                # 两段参数：explorer 会拼成 /select,<path>，路径带空格也能选中
                subprocess.Popen(["explorer", "/select,", str(target)])
        else:
            subprocess.run(["xdg-open", str(target if target.is_dir() else target.parent)], check=False)
        return True
    except OSError:
        return False


def trash_root(root: Path) -> Path:
    return (root / TRASH_REL).resolve()


def _load_trash_manifest(root: Path) -> dict:
    man = trash_root(root) / "manifest.json"
    if not man.is_file():
        return {"items": []}
    try:
        data = json.loads(man.read_text(encoding="utf-8"))
    except Exception:
        return {"items": []}
    if not isinstance(data, dict):
        return {"items": []}
    items = data.get("items")
    if not isinstance(items, list):
        data["items"] = []
    return data


def _save_trash_manifest(root: Path, data: dict) -> None:
    trash = trash_root(root)
    trash.mkdir(parents=True, exist_ok=True)
    man = trash / "manifest.json"
    man.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _unique_trash_dest(trash: Path, rel: str) -> Path:
    """Keep original relative layout under trash; collide → append timestamp."""
    rel_norm = rel.replace("\\", "/").lstrip("/")
    dest = trash / rel_norm
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return dest.with_name(f"{stem}__deleted_{stamp}{suffix}")


def delete_paths(root: Path, paths: list[str]) -> dict:
    """Move images into local trash (recoverable). Never hard-delete from workbench."""
    deleted: list[str] = []
    trashed: list[dict] = []
    errors: list[dict] = []
    root_r = root.resolve()
    trash = trash_root(root_r)
    trash.mkdir(parents=True, exist_ok=True)
    # marker so humans know what this folder is
    readme = trash / "README.txt"
    if not readme.is_file():
        readme.write_text(
            "Workbench trash / 工作台垃圾桶\n"
            "Deleted images are moved here (not git-committed).\n"
            "Put a file back to its original relative path under the project root to restore.\n"
            "Deleting files inside this folder permanently removes them.\n",
            encoding="utf-8",
        )
    manifest = _load_trash_manifest(root_r)
    items = manifest.setdefault("items", [])
    if not isinstance(items, list):
        items = []
        manifest["items"] = items

    for raw in paths:
        target = _safe_under_root(root_r, str(raw or ""), must_exist=True)
        if not target or not target.is_file():
            errors.append({"path": raw, "error": "not found"})
            continue
        if target.suffix.lower() not in IMAGE_SUFFIXES:
            errors.append({"path": raw, "error": "not an image"})
            continue
        try:
            rel = str(target.relative_to(root_r)).replace("\\", "/")
        except ValueError:
            errors.append({"path": raw, "error": "outside root"})
            continue
        rel_n = rel.replace("\\", "/")
        # already in trash — ignore
        if rel_n.startswith(TRASH_REL + "/"):
            errors.append({"path": raw, "error": "already in trash"})
            continue
        if any(rel_n.startswith(p) for p in PROTECTED_PREFIXES if p != TRASH_REL + "/"):
            errors.append({"path": raw, "error": "protected teaching asset"})
            continue
        try:
            dest = _unique_trash_dest(trash, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(dest))
            trash_rel = str(dest.relative_to(root_r)).replace("\\", "/")
            entry = {
                "original": rel,
                "trash": trash_rel,
                "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            items.append(entry)
            deleted.append(rel)
            trashed.append(entry)
        except OSError as exc:
            errors.append({"path": raw, "error": str(exc)})

    if trashed:
        try:
            _save_trash_manifest(root_r, manifest)
        except OSError:
            pass
        # 同步踢掉热更新索引，否则刷新/hotReload 会把已删图又加载回来
        try:
            purge_paths_from_atlas_sidecar(root_r, deleted)
        except OSError:
            pass

    return {
        "ok": len(errors) == 0 and len(deleted) > 0,
        "deleted": deleted,
        "trashed": trashed,
        "trash_dir": TRASH_REL,
        "errors": errors,
        "service": SERVICE_NAME,
        "mode": "trash",
    }


def purge_paths_from_atlas_sidecar(root: Path, paths: list[str]) -> int:
    """Remove deleted relatives from .memory-art/atlas_data.json so refresh stays clean."""
    data_path = (root / ".memory-art" / "atlas_data.json").resolve()
    if not data_path.is_file() or not paths:
        return 0
    try:
        data_path.relative_to(root.resolve())
    except ValueError:
        return 0
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    banned = {str(p or "").replace("\\", "/").lstrip("/") for p in paths if str(p or "").strip()}
    if not banned:
        return 0
    removed = 0
    assets = data.get("assets")
    if isinstance(assets, dict):
        for key in list(assets.keys()):
            kn = str(key).replace("\\", "/")
            info = assets.get(key) if isinstance(assets.get(key), dict) else {}
            pk = str((info or {}).get("path") or "").replace("\\", "/")
            if kn in banned or pk in banned:
                del assets[key]
                removed += 1
    idx = data.get("index_images")
    if isinstance(idx, list):
        keep = []
        for it in idx:
            if not isinstance(it, dict):
                continue
            p = str(it.get("path") or "").replace("\\", "/")
            if p in banned:
                removed += 1
                continue
            keep.append(it)
        data["index_images"] = keep
    if removed:
        data_path.write_text(
            json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
            encoding="utf-8",
        )
    return removed



def promote_final(
    root: Path,
    *,
    source_path: str,
    final_path: str = "",
    session_id: str = "",
    round_num: Any = None,
) -> dict:
    """Copy a process/candidate image over the final delivery slot; keep converge rounds."""
    root_r = root.resolve()
    src = _safe_under_root(root_r, source_path, must_exist=True)
    if not src or not src.is_file() or src.suffix.lower() not in IMAGE_SUFFIXES:
        return {"ok": False, "error": "source not found", "service": SERVICE_NAME}

    dst_rel = (final_path or "").strip().replace("\\", "/")
    sess_path: Path | None = None
    sess_doc: dict[str, Any] | None = None
    if session_id:
        cand = root_r / ".memory-art" / "converge" / f"{session_id}.json"
        if cand.is_file():
            sess_path = cand
            try:
                loaded = json.loads(cand.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    sess_doc = loaded
            except Exception:
                sess_doc = None
            if not dst_rel and isinstance(sess_doc, dict):
                dst_rel = str(
                    sess_doc.get("winner_image")
                    or sess_doc.get("best_image")
                    or sess_doc.get("final_image")
                    or ""
                ).replace("\\", "/")
                # normalize abs -> rel
                if dst_rel:
                    try:
                        p = Path(dst_rel)
                        if p.is_absolute():
                            dst_rel = str(p.resolve().relative_to(root_r)).replace("\\", "/")
                    except Exception:
                        pass

    if not dst_rel:
        # 默认：同目录把源文件名里的 _rN 换成 _final，后缀沿用源
        stem = re.sub(r"[_-]r\d{1,2}$", "", src.stem, flags=re.I)
        dst_rel = str((src.parent / f"{stem}_final{src.suffix}").relative_to(root_r)).replace("\\", "/")

    dst = _safe_under_root(root_r, dst_rel, must_exist=False)
    if dst is None:
        # parent must stay under root
        try:
            trial = (root_r / dst_rel).resolve()
            trial.relative_to(root_r)
            dst = trial
        except Exception:
            return {"ok": False, "error": "final path outside root", "service": SERVICE_NAME}
    if dst.suffix.lower() not in IMAGE_SUFFIXES:
        return {"ok": False, "error": "final not an image", "service": SERVICE_NAME}

    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and dst.resolve() != src.resolve():
            backup_dir = root_r / ".memory-art" / "_final_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d_%H%M%S")
            backup = backup_dir / f"{dst.stem}_{stamp}{dst.suffix}"
            shutil.copy2(dst, backup)
        shutil.copy2(src, dst)
    except OSError as exc:
        return {"ok": False, "error": str(exc), "service": SERVICE_NAME}

    src_rel = str(src.relative_to(root_r)).replace("\\", "/")
    final_rel = str(dst.relative_to(root_r)).replace("\\", "/")

    if sess_path and isinstance(sess_doc, dict):
        sess_doc["winner_image"] = final_rel
        sess_doc["final_image"] = final_rel
        sess_doc["promoted_from"] = src_rel
        if round_num is not None:
            sess_doc["promoted_round"] = round_num
        try:
            sess_path.write_text(
                json.dumps(sess_doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    return {
        "ok": True,
        "source_path": src_rel,
        "final_path": final_rel,
        "session_id": session_id or "",
        "round": round_num,
        "mtime": dst.stat().st_mtime,
        "service": SERVICE_NAME,
    }


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

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        _cors(self)
        self.end_headers()

    def _serve_static(self, url_path: str) -> None:
        """Serve workbench HTML/assets over http so delete/reveal work (file:// POST 常被拦)."""
        raw = urllib.parse.unquote(url_path or "/")
        if raw in ("", "/"):
            raw = "/art-atlas.html"
        rel = raw.lstrip("/").replace("\\", "/")
        if not rel or ".." in rel.split("/"):
            self._json(404, {"ok": False, "error": "not found", "service": SERVICE_NAME})
            return
        low = rel.lower()
        if any(low.startswith(p) or ("/" + p) in ("/" + low) for p in _STATIC_BLOCK_PREFIXES):
            self._json(403, {"ok": False, "error": "forbidden", "service": SERVICE_NAME})
            return
        target = _safe_under_root(self.root, rel, must_exist=True)
        if not target or not target.is_file():
            self._json(404, {"ok": False, "error": "not found", "service": SERVICE_NAME})
            return
        try:
            data = target.read_bytes()
        except OSError:
            self._json(500, {"ok": False, "error": "read failed", "service": SERVICE_NAME})
            return
        ctype = _STATIC_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        _cors(self)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        # 工作台 HTML 经常重建；静态图可短缓存
        if target.suffix.lower() in {".html", ".js", ".json"}:
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/api/ping", "/ping"):
            self._json(
                200,
                {
                    "ok": True,
                    "service": SERVICE_NAME,
                    "apis": ["reveal", "delete", "promote", "trash", "static"],
                    "root": str(self.root),
                    "pid": os.getpid(),
                    "workbench": f"http://127.0.0.1:{self.server.server_address[1]}/art-atlas.html",
                },
            )
            return
        if parsed.path in ("/api/reveal", "/reveal"):
            qs = urllib.parse.parse_qs(parsed.query)
            target = self._resolve_reveal_target((qs.get("path") or [""])[0])
            if not target:
                self._json(404, {"ok": False, "error": "not found", "service": SERVICE_NAME})
                return
            ok = reveal_path(target)
            self._json(200 if ok else 500, {"ok": ok, "path": str(target), "service": SERVICE_NAME})
            return
        # 非 /api/* 走静态托管（art-atlas.html / assets / thumbs）
        if not parsed.path.startswith("/api/"):
            self._serve_static(parsed.path)
            return
        self._json(404, {"ok": False, "error": "unknown", "service": SERVICE_NAME})

    def _resolve_reveal_target(self, raw: str) -> Path | None:
        """Allow opening trash/guide dirs even before first use (mkdir trash)."""
        rel = (raw or "").strip().replace("\\", "/").lstrip("/")
        target = _safe_under_root(self.root, rel, must_exist=False)
        if not target:
            return None
        if not target.exists():
            # 垃圾桶首次打开：自动建好空目录，方便美术找回来
            if rel.rstrip("/") == TRASH_REL or rel.startswith(TRASH_REL + "/"):
                try:
                    trash_root(self.root).mkdir(parents=True, exist_ok=True)
                except OSError:
                    return None
                target = trash_root(self.root) if rel.rstrip("/") == TRASH_REL else target
                if not target.exists():
                    return None
            else:
                return None
        return target

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        payload = self._read_json()
        if parsed.path in ("/api/reveal", "/reveal"):
            target = self._resolve_reveal_target(str(payload.get("path") or ""))
            if not target:
                self._json(404, {"ok": False, "error": "not found", "service": SERVICE_NAME})
                return
            ok = reveal_path(target)
            self._json(200 if ok else 500, {"ok": ok, "path": str(target), "service": SERVICE_NAME})
            return
        if parsed.path in ("/api/delete", "/delete"):
            raw_paths = payload.get("paths") or payload.get("path") or []
            if isinstance(raw_paths, str):
                raw_paths = [raw_paths]
            if not isinstance(raw_paths, list) or not raw_paths:
                self._json(400, {"ok": False, "error": "paths required", "service": SERVICE_NAME})
                return
            result = delete_paths(self.root, [str(x) for x in raw_paths])
            code = 200 if result.get("deleted") else 404
            if result.get("errors") and result.get("deleted"):
                code = 207
            self._json(code, result)
            return
        if parsed.path in ("/api/promote", "/promote", "/api/promote_final"):
            result = promote_final(
                self.root,
                source_path=str(payload.get("source_path") or payload.get("path") or ""),
                final_path=str(payload.get("final_path") or ""),
                session_id=str(payload.get("session_id") or ""),
                round_num=payload.get("round"),
            )
            self._json(200 if result.get("ok") else 400, result)
            return
        self._json(404, {"ok": False, "error": "unknown", "service": SERVICE_NAME})


def run_server(root: Path, port: int = DEFAULT_PORT) -> None:
    RevealHandler.root = root.resolve()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), RevealHandler)
    httpd.serve_forever()


def ping_server(port: int = DEFAULT_PORT, timeout: float = 0.4) -> bool:
    """True only when our service answers (ignore unrelated listeners on the port)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=timeout) as resp:
            if int(getattr(resp, "status", 200) or 200) != 200:
                return False
            data = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
            if not (bool(data.get("ok")) and data.get("service") == SERVICE_NAME):
                return False
            # 旧守护缺 trash/promote 时当作不可用，迫使换端口拉起新进程
            apis = data.get("apis")
            return isinstance(apis, list) and ("promote" in apis) and ("trash" in apis)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        return False


def _port_free(port: int) -> bool:
    """Bind check without SO_REUSEADDR — Windows REUSEADDR can lie about free ports."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _pick_listen_port(preferred: int = DEFAULT_PORT) -> int:
    for base in (preferred, DEFAULT_PORT, 8765):
        for candidate in range(base, base + 48):
            if ping_server(candidate):
                return candidate
            if _port_free(candidate):
                return candidate
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])
    finally:
        s.close()


def _script_mtime(root: Path) -> float:
    try:
        return float((root / "atlas_reveal.py").resolve().stat().st_mtime)
    except OSError:
        return 0.0


def write_port_files(
    root: Path,
    port: int,
    pid: int | None = None,
    *,
    stamp_code: bool = False,
) -> None:
    mem = root / ".memory-art"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "atlas_reveal.port").write_text(str(port), encoding="utf-8")
    if pid is not None:
        (mem / "atlas_reveal.pid").write_text(str(pid), encoding="utf-8")
    # 只有拉起新进程时盖章，避免复用旧守护时误刷新 stamp
    if stamp_code or pid is not None:
        (mem / "atlas_reveal.code_mtime").write_text(str(_script_mtime(root)), encoding="utf-8")


def _daemon_matches_current_code(root: Path) -> bool:
    """False when atlas_reveal.py is newer than the running daemon stamp."""
    stamp = root / ".memory-art" / "atlas_reveal.code_mtime"
    if not stamp.is_file():
        return False
    try:
        started = float((stamp.read_text(encoding="utf-8") or "0").strip() or "0")
    except ValueError:
        return False
    cur = _script_mtime(root)
    # allow tiny FS timestamp jitter
    return started > 0 and cur > 0 and cur <= started + 1.0


def _stop_daemon(root: Path, port: int) -> None:
    pid_file = root / ".memory-art" / "atlas_reveal.pid"
    pid = 0
    if pid_file.is_file():
        try:
            pid = int((pid_file.read_text(encoding="utf-8") or "0").strip() or "0")
        except ValueError:
            pid = 0
    if pid > 0:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                os.kill(pid, 15)
        except OSError:
            pass
    # wait until port frees or ping dies
    for _ in range(40):
        if not ping_server(port, timeout=0.2):
            break
        time.sleep(0.05)


def ensure_reveal_daemon(root: Path, port: int = DEFAULT_PORT) -> int:
    """Ensure localhost reveal bridge is up; return port (0 if failed)."""
    root = root.resolve()
    # Prefer previously written port if it is still our service AND code is current
    port_file = root / ".memory-art" / "atlas_reveal.port"
    if port_file.is_file():
        try:
            old = int((port_file.read_text(encoding="utf-8") or "0").strip() or "0")
        except ValueError:
            old = 0
        if old and ping_server(old):
            if _daemon_matches_current_code(root):
                write_port_files(root, old)  # 不盖章
                return old
            _stop_daemon(root, old)

    if ping_server(port):
        if _daemon_matches_current_code(root):
            write_port_files(root, port)
            return port
        _stop_daemon(root, port)

    chosen = _pick_listen_port(port)
    if ping_server(chosen) and _daemon_matches_current_code(root):
        write_port_files(root, chosen)
        return chosen
    if ping_server(chosen) and not _daemon_matches_current_code(root):
        _stop_daemon(root, chosen)
        chosen = _pick_listen_port(port)

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
    for _ in range(50):
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
