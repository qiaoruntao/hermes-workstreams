"""``pre_llm_call`` context: the linked workstream's FOCUS.md, only when new or changed."""
from __future__ import annotations

import contextlib
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

from . import core

SKILL_REF = "hermes-workstreams:workstream-focus"
_MAX_LISTED = 20


def stored_session_cwd(session_id: str) -> str:
    """The session's persisted cwd from state.db. Plugins may run in an isolated plugin host, where
    the agent's cwd contextvar is absent, so the durable session row is the reliable source."""
    if not session_id:
        return ""
    try:
        from hermes_constants import get_hermes_home
        uri = (get_hermes_home() / "state.db").as_uri() + "?mode=ro"
        with contextlib.closing(sqlite3.connect(uri, uri=True, timeout=2)) as conn:
            row = conn.execute("SELECT cwd FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return str(row[0]) if row and row[0] else ""
    except Exception:
        return ""


def current_cwd(session_id: str = "") -> str:
    """Stored session cwd, then the in-process session contextvar."""
    cwd = stored_session_cwd(session_id)
    if cwd:
        return cwd
    try:
        from agent.runtime_cwd import scoped_session_cwd
        return scoped_session_cwd()
    except Exception:
        return ""


class FocusInjector:
    def __init__(
        self,
        cwd_fn: Callable[[str], str] = current_cwd,
        settings_fn: Callable[[], dict[str, Any]] = core.settings,
    ) -> None:
        self._cwd_fn = cwd_fn
        self._settings_fn = settings_fn
        self._shown: dict[str, tuple[str, str]] = {}
        self._lock = threading.Lock()

    def __call__(self, session_id: str = "", is_first_turn: bool = False, **_: Any) -> dict | None:
        config = self._settings_fn()
        root = core.workstreams_root(config)
        workstream = core.find_workstream(self._cwd_fn(session_id), root)
        if workstream is None:
            return self._unlinked_hint(root) if is_first_turn else None
        doc = core.read_focus(workstream)
        marker = (str(workstream), doc.digest)
        with self._lock:
            if self._shown.get(session_id) == marker:
                return None
            self._shown[session_id] = marker
        return {"context": self._focus_block(workstream, doc, config)}

    def _unlinked_hint(self, root: Path) -> dict | None:
        names = core.list_workstreams(root)
        listed = ", ".join(names[:_MAX_LISTED]) + (" …" if len(names) > _MAX_LISTED else "")
        existing = f" Existing: {listed}." if names else ""
        return {"context": (
            f"[Workstreams] Multi-session workstreams live in {root}.{existing} If this request continues "
            f"one or starts a new multi-session issue, load skill `{SKILL_REF}` and link this session; "
            "otherwise ignore this note.")}

    @staticmethod
    def _focus_block(workstream: Path, doc: core.FocusDoc, config: dict[str, Any]) -> str:
        max_words, max_lines = core.budget_limits(config)
        header = f"[Workstream: {workstream.name}] This session is linked to {workstream}."
        if not doc.exists:
            return f"{header} {core.FOCUS_FILE} is missing; create it per skill `{SKILL_REF}`."
        over = doc.words > max_words or doc.lines > max_lines
        budget = (f" It is OVER budget ({doc.words}/{max_words} words, {doc.lines}/{max_lines} lines): prune it."
                  if over else "")
        return (f"{header} Current {doc.path} (shown when it changes):{budget}\n"
                f"<focus>\n{doc.content.strip()}\n</focus>\n"
                f"Keep it current per skill `{SKILL_REF}`; read other files in the workstream dir only when needed.")
