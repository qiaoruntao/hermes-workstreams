"""Workstream resolution and FOCUS.md access — no Hermes runtime required except for settings."""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLUGIN_ID = "hermes-workstreams"
FOCUS_FILE = "FOCUS.md"
DEFAULT_ROOT = "~/hermes-workstreams"
DEFAULT_MAX_WORDS = 100
DEFAULT_MAX_LINES = 12

TASK_RE = re.compile(r"^(\s*[-*+]\s+\[)([ xX])(\].*)$")


class FocusConflict(Exception):
    """FOCUS.md changed since the caller read it."""


def settings() -> dict[str, Any]:
    """``plugins.entries.hermes-workstreams.settings`` from config.yaml, or ``{}``."""
    try:
        from hermes_cli.config import load_config_readonly
        cfg = load_config_readonly() or {}
    except Exception:
        return {}
    entry = ((cfg.get("plugins") or {}).get("entries") or {}).get(PLUGIN_ID) or {}
    value = entry.get("settings") if isinstance(entry, dict) else None
    return value if isinstance(value, dict) else {}


def workstreams_root(config: dict[str, Any] | None = None) -> Path:
    raw = (config if config is not None else settings()).get("workstreams_root") or DEFAULT_ROOT
    return Path(str(raw)).expanduser().resolve()


def budget_limits(config: dict[str, Any] | None = None) -> tuple[int, int]:
    cfg = config if config is not None else settings()
    try:
        return int(cfg.get("max_words") or DEFAULT_MAX_WORDS), int(cfg.get("max_lines") or DEFAULT_MAX_LINES)
    except (TypeError, ValueError):
        return DEFAULT_MAX_WORDS, DEFAULT_MAX_LINES


def find_workstream(cwd: str | os.PathLike[str] | None, root: Path) -> Path | None:
    """The workstream dir owning *cwd*: the direct child of *root* that is or contains cwd."""
    if not cwd or not str(cwd).strip():
        return None
    try:
        target = Path(cwd).expanduser().resolve()
        rel = target.relative_to(root)
    except (OSError, ValueError):
        return None
    if not rel.parts:
        return None
    candidate = root / rel.parts[0]
    return candidate if candidate.is_dir() else None


def list_workstreams(root: Path) -> list[str]:
    try:
        return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    except OSError:
        return []


@dataclass(frozen=True)
class FocusDoc:
    path: Path
    exists: bool
    content: str
    mtime_ns: int

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    @property
    def lines(self) -> int:
        return sum(1 for line in self.content.splitlines() if line.strip())

    @property
    def words(self) -> int:
        return len(self.content.split())


def read_focus(workstream: Path) -> FocusDoc:
    path = workstream / FOCUS_FILE
    try:
        stat = path.stat()
        return FocusDoc(path, True, path.read_text(encoding="utf-8"), stat.st_mtime_ns)
    except FileNotFoundError:
        return FocusDoc(path, False, "", 0)


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".focus-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def save_focus(workstream: Path, content: str, expected_mtime_ns: int) -> FocusDoc:
    """Replace FOCUS.md with *content* if it is unchanged since *expected_mtime_ns* (0 = must not exist)."""
    doc = read_focus(workstream)
    if doc.mtime_ns != expected_mtime_ns:
        raise FocusConflict(str(doc.path))
    _atomic_write(doc.path, content)
    return read_focus(workstream)


def toggle_task(workstream: Path, line_index: int, checked: bool, expected_mtime_ns: int) -> FocusDoc:
    """Set the checkbox on *line_index* (0-based, raw lines) if FOCUS.md is unchanged."""
    doc = read_focus(workstream)
    if not doc.exists:
        raise FileNotFoundError(doc.path)
    if doc.mtime_ns != expected_mtime_ns:
        raise FocusConflict(str(doc.path))
    lines = doc.content.splitlines(keepends=True)
    if not 0 <= line_index < len(lines):
        raise ValueError("line out of range")
    body = lines[line_index].rstrip("\r\n")
    ending = lines[line_index][len(body):]
    match = TASK_RE.match(body)
    if match is None:
        raise ValueError("line is not a task")
    lines[line_index] = f"{match.group(1)}{'x' if checked else ' '}{match.group(3)}{ending}"
    _atomic_write(doc.path, "".join(lines))
    return read_focus(workstream)
