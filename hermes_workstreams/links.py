"""Pending session → workstream links. The agent records one; the Desktop panel performs the real move
(``session.workspace.move``, the same call as the sidebar's Move to project) once the turn is idle."""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from . import core

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
STARTER = "# {name}\n\n- [ ] {task}\n"
_lock = threading.Lock()


def links_path() -> Path:
    try:
        from plugins.plugin_storage import plugin_data_dir
        return plugin_data_dir(core.PLUGIN_ID) / "links.json"
    except Exception:
        from hermes_constants import get_hermes_home
        path = get_hermes_home() / "plugin-data" / core.PLUGIN_ID
        path.mkdir(parents=True, exist_ok=True)
        return path / "links.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _store(path: Path, data: dict[str, Any]) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".links-", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1)
    os.replace(tmp, path)


def request_link(session_id: str, workstream: Path, path: Path | None = None) -> None:
    path = path or links_path()
    with _lock:
        data = _load(path)
        data[session_id] = {"slug": workstream.name, "cwd": str(workstream), "requestedAt": int(time.time())}
        _store(path, data)


def pending_link(session_id: str, path: Path | None = None) -> dict | None:
    entry = _load(path or links_path()).get(session_id)
    return entry if isinstance(entry, dict) and entry.get("cwd") else None


def all_pending(path: Path | None = None, *, max_age_s: int = 6 * 3600) -> list[dict]:
    """Every pending link not older than *max_age_s* (stale ones are dropped)."""
    path = path or links_path()
    now = int(time.time())
    with _lock:
        data = _load(path)
        fresh = {k: v for k, v in data.items()
                 if isinstance(v, dict) and v.get("cwd") and now - int(v.get("requestedAt") or 0) <= max_age_s}
        if len(fresh) != len(data):
            _store(path, fresh)
    return [{"sessionId": k, "slug": v["slug"], "cwd": v["cwd"]} for k, v in fresh.items()]


def clear_link(session_id: str, path: Path | None = None) -> None:
    path = path or links_path()
    with _lock:
        data = _load(path)
        if data.pop(session_id, None) is not None:
            _store(path, data)


def ensure_workstream(root: Path, slug: str, *, name: str = "", task: str = "", icon: str = "",
                      color: str = "") -> tuple[Path, bool]:
    """Return (dir, created). Creates the dir, a starter FOCUS.md and the Hermes Project (only this folder)."""
    if not SLUG_RE.match(slug):
        raise ValueError("slug must be lowercase kebab-case (a-z, 0-9, -), max 64 chars")
    workstream = root / slug
    created = not workstream.exists()
    workstream.mkdir(parents=True, exist_ok=True)
    focus = workstream / core.FOCUS_FILE
    if not focus.exists():
        focus.write_text(STARTER.format(name=name or slug, task=task or "Define the goal"), encoding="utf-8")
    from hermes_cli import projects_db as pdb
    with pdb.connect_closing() as conn:
        if pdb.find_by_primary_path(conn, str(workstream)) is None:
            pdb.create_project(conn, name=name or slug, slug=slug, folders=[str(workstream)],
                               primary_path=str(workstream), icon=icon or None, color=color or None)
    return workstream, created
