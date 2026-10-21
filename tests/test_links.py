from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_workstreams import core, links, tool


class LinkTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.root = base / "workstreams"
        self.root.mkdir()
        self.links_file = base / "links.json"
        self.projects_db = base / "projects.db"
        from hermes_cli import projects_db as pdb
        real_connect = pdb.connect_closing
        patches = [
            patch.object(links, "links_path", return_value=self.links_file),
            patch.object(core, "settings", return_value={"workstreams_root": str(self.root)}),
            patch.object(pdb, "connect_closing", lambda db_path=None: real_connect(self.projects_db)),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_create_makes_dir_focus_project_and_pending_link(self) -> None:
        out = json.loads(tool.handle({"slug": "smb-drop", "create": True, "name": "SMB drop",
                                      "first_task": "Collect logs", "icon": "bug"}, session_id="s1"))
        self.assertTrue(out["success"] and out["created"])
        ws = self.root / "smb-drop"
        self.assertIn("- [ ] Collect logs", (ws / "FOCUS.md").read_text())
        from hermes_cli import projects_db as pdb
        with pdb.connect_closing() as conn:
            project = pdb.find_by_primary_path(conn, str(ws))
        self.assertEqual((project.slug, project.icon, [f.path for f in project.folders]), ("smb-drop", "bug", [str(ws)]))
        self.assertEqual(links.pending_link("s1")["cwd"], str(ws))

    def test_create_is_idempotent_and_keeps_existing_focus(self) -> None:
        tool.handle({"slug": "x", "create": True}, session_id="s1")
        (self.root / "x" / "FOCUS.md").write_text("# mine\n")
        out = json.loads(tool.handle({"slug": "x", "create": True}, session_id="s2"))
        self.assertTrue(out["success"])
        self.assertFalse(out["created"])
        self.assertEqual((self.root / "x" / "FOCUS.md").read_text(), "# mine\n")

    def test_link_existing_and_unknown(self) -> None:
        tool.handle({"slug": "x", "create": True}, session_id="s1")
        self.assertTrue(json.loads(tool.handle({"slug": "x", "create": False}, session_id="s2"))["success"])
        missing = json.loads(tool.handle({"slug": "nope", "create": False}, session_id="s2"))
        self.assertFalse(missing["success"])
        self.assertEqual(missing["existing"], ["x"])

    def test_rejects_bad_slug_and_missing_session(self) -> None:
        self.assertFalse(json.loads(tool.handle({"slug": "Bad Slug", "create": True}, session_id="s1"))["success"])
        self.assertFalse(json.loads(tool.handle({"slug": "x", "create": True}))["success"])

    def test_clear_link(self) -> None:
        links.request_link("s1", self.root / "x")
        links.clear_link("s1")
        self.assertIsNone(links.pending_link("s1"))


if __name__ == "__main__":
    unittest.main()
