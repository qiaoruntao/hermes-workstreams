from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hermes_workstreams import core
from hermes_workstreams.inject import FocusInjector

FOCUS = "# HLS spike\n- [ ] check panel\n- [x] reproduce\nRepos: ~/projects/android_endpoint\n"


class CoreTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "workstreams"
        self.ws = self.root / "hls-spike"
        (self.ws / "notes").mkdir(parents=True)
        (self.ws / core.FOCUS_FILE).write_text(FOCUS, encoding="utf-8")

    def test_find_workstream_from_dir_and_subdir(self) -> None:
        self.assertEqual(core.find_workstream(self.ws, self.root), self.ws)
        self.assertEqual(core.find_workstream(self.ws / "notes", self.root), self.ws)

    def test_find_workstream_rejects_root_outside_and_empty(self) -> None:
        self.assertIsNone(core.find_workstream(self.root, self.root))
        self.assertIsNone(core.find_workstream(self.root.parent, self.root))
        self.assertIsNone(core.find_workstream("", self.root))

    def test_toggle_task_rewrites_only_that_checkbox(self) -> None:
        doc = core.read_focus(self.ws)
        core.toggle_task(self.ws, 1, True, doc.mtime_ns)
        lines = core.read_focus(self.ws).content.splitlines()
        self.assertEqual(lines[1], "- [x] check panel")
        self.assertEqual(lines[2], "- [x] reproduce")
        doc = core.read_focus(self.ws)
        core.toggle_task(self.ws, 2, False, doc.mtime_ns)
        self.assertEqual(core.read_focus(self.ws).content, FOCUS.replace("[ ] check", "[x] check").replace("[x] repro", "[ ] repro"))

    def test_toggle_task_refuses_stale_version_and_non_task(self) -> None:
        with self.assertRaises(core.FocusConflict):
            core.toggle_task(self.ws, 1, True, 1)
        doc = core.read_focus(self.ws)
        with self.assertRaises(ValueError):
            core.toggle_task(self.ws, 0, True, doc.mtime_ns)

    def test_save_focus_requires_current_version(self) -> None:
        doc = core.read_focus(self.ws)
        core.save_focus(self.ws, "# New\n", doc.mtime_ns)
        self.assertEqual(core.read_focus(self.ws).content, "# New\n")
        with self.assertRaises(core.FocusConflict):
            core.save_focus(self.ws, "# Stale\n", doc.mtime_ns)

    def test_budget_counts(self) -> None:
        doc = core.read_focus(self.ws)
        self.assertEqual(doc.lines, 4)
        self.assertEqual(doc.words, len(FOCUS.split()))


class InjectorTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "workstreams"
        self.ws = self.root / "hls-spike"
        self.ws.mkdir(parents=True)
        (self.ws / core.FOCUS_FILE).write_text(FOCUS, encoding="utf-8")
        self.cwd = str(self.ws)
        self.injector = FocusInjector(cwd_fn=lambda _sid: self.cwd,
                                      settings_fn=lambda: {"workstreams_root": str(self.root)})

    def test_injects_focus_once_until_changed(self) -> None:
        first = self.injector(session_id="s1", is_first_turn=True)
        self.assertIn("check panel", first["context"])
        self.assertIn("hls-spike", first["context"])
        self.assertIsNone(self.injector(session_id="s1"))
        (self.ws / core.FOCUS_FILE).write_text(FOCUS + "- [ ] new\n", encoding="utf-8")
        self.assertIn("- [ ] new", self.injector(session_id="s1")["context"])

    def test_sessions_are_independent(self) -> None:
        self.assertIsNotNone(self.injector(session_id="s1"))
        self.assertIsNotNone(self.injector(session_id="s2"))

    def test_switching_workstream_reinjects(self) -> None:
        other = self.root / "other"
        other.mkdir()
        (other / core.FOCUS_FILE).write_text("# Other\n", encoding="utf-8")
        self.injector(session_id="s1")
        self.cwd = str(other)
        self.assertIn("# Other", self.injector(session_id="s1")["context"])

    def test_unlinked_session_gets_hint_only_on_first_turn(self) -> None:
        self.cwd = str(self.root.parent)
        hint = self.injector(session_id="s1", is_first_turn=True)
        self.assertIn("hls-spike", hint["context"])
        self.assertIsNone(self.injector(session_id="s1", is_first_turn=False))

    def test_over_budget_is_flagged(self) -> None:
        (self.ws / core.FOCUS_FILE).write_text("word " * 200, encoding="utf-8")
        self.assertIn("OVER budget", self.injector(session_id="s1")["context"])

    def test_missing_focus_asks_to_create(self) -> None:
        (self.ws / core.FOCUS_FILE).unlink()
        self.assertIn("missing", self.injector(session_id="s1")["context"])


class StoredCwdTests(unittest.TestCase):
    def test_reads_cwd_from_state_db(self) -> None:
        import sqlite3
        from unittest.mock import patch
        from hermes_workstreams import inject
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with sqlite3.connect(home / "state.db") as conn:
                conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, cwd TEXT)")
                conn.execute("INSERT INTO sessions VALUES ('s1', '/work/ws')")
            with patch("hermes_constants.get_hermes_home", return_value=home):
                self.assertEqual(inject.stored_session_cwd("s1"), "/work/ws")
                self.assertEqual(inject.stored_session_cwd("missing"), "")


if __name__ == "__main__":
    unittest.main()
