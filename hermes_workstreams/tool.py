"""Agent tool ``workstream_link``: create (if needed) and link the calling session to a workstream."""
from __future__ import annotations

import json
from typing import Any

from . import core, links

SCHEMA = {
    "name": "workstream_link",
    "description": (
        "Link THIS chat to a multi-session workstream (a Hermes Project under the workstreams root), creating "
        "it first if missing. The Desktop panel moves the chat into the project right after this turn ends. "
        "Use only per skill hermes-workstreams:workstream-focus."),
    "parameters": {
        "type": "object",
        "properties": {
            "slug": {"type": "string", "description": "kebab-case workstream id, e.g. 'rp5-samba-disconnects'"},
            "create": {"type": "boolean", "description": "true to create a new workstream; false to link an existing one"},
            "name": {"type": "string", "description": "create: human project name"},
            "first_task": {"type": "string", "description": "create: first todo for the starter FOCUS.md"},
            "icon": {"type": "string", "description": "create: codicon name, e.g. bug, rocket, beaker"},
        },
        "required": ["slug", "create"],
    },
}


def handle(args: dict[str, Any], session_id: str = "", **_: Any) -> str:
    slug = str(args.get("slug") or "").strip()
    root = core.workstreams_root()
    if not session_id:
        return json.dumps({"success": False, "error": "no calling session id"})
    if args.get("create"):
        try:
            workstream, created = links.ensure_workstream(
                root, slug, name=str(args.get("name") or ""), task=str(args.get("first_task") or ""),
                icon=str(args.get("icon") or ""))
        except ValueError as exc:
            return json.dumps({"success": False, "error": str(exc)})
    else:
        workstream, created = root / slug, False
        if not (workstream / core.FOCUS_FILE).exists():
            existing = core.list_workstreams(root)
            return json.dumps({"success": False, "error": f"no workstream '{slug}'", "existing": existing})
    links.request_link(session_id, workstream)
    return json.dumps({
        "success": True, "created": created, "workstream": str(workstream),
        "focus_file": str(workstream / core.FOCUS_FILE),
        "linked": "pending",
        "note": ("The Desktop panel moves this chat into the project when this turn ends; until then your cwd is "
                 "unchanged, so use absolute paths. Outside Desktop, ask the user to use Move to project."),
    })
