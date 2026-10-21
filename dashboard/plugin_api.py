from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_workstreams import core, links

router = APIRouter()


def _project_info(workstream: Path) -> dict | None:
    try:
        from hermes_cli import projects_db as pdb
        with pdb.connect_closing() as conn:
            project = pdb.project_for_path(conn, str(workstream))
    except Exception:
        return None
    if project is None:
        return None
    return {"id": project.id, "slug": project.slug, "name": project.name,
            "icon": project.icon, "color": project.color}


def _resolve(body: object) -> Path | None:
    if not isinstance(body, dict):
        return None
    cwd = ""
    session_id = body.get("sessionId")
    if isinstance(session_id, str) and session_id:
        from hermes_workstreams.inject import stored_session_cwd
        cwd = stored_session_cwd(session_id)
    if not cwd and isinstance(body.get("cwd"), str):
        cwd = body["cwd"]
    return core.find_workstream(cwd or None, core.workstreams_root())


def _payload(workstream: Path | None) -> dict:
    if workstream is None:
        return {"workstream": None}
    doc = core.read_focus(workstream)
    max_words, max_lines = core.budget_limits()
    return {
        "workstream": {"slug": workstream.name, "path": str(workstream), "project": _project_info(workstream)},
        "focus": {"path": str(doc.path), "exists": doc.exists, "content": doc.content, "mtimeNs": str(doc.mtime_ns),
                  "words": doc.words, "lines": doc.lines, "maxWords": max_words, "maxLines": max_lines,
                  "overBudget": doc.words > max_words or doc.lines > max_lines},
    }


@router.post("/focus")
def get_focus(body: dict) -> dict:
    payload = _payload(_resolve(body))
    session_id = body.get("sessionId") if isinstance(body, dict) else None
    if isinstance(session_id, str) and session_id:
        pending = links.pending_link(session_id)
        current = payload["workstream"]["path"] if payload["workstream"] else None
        if pending and pending["cwd"] == current:
            links.clear_link(session_id)  # already moved (e.g. via the sidebar)
        elif pending:
            payload["pendingLink"] = {"slug": pending["slug"], "cwd": pending["cwd"]}
    return payload


@router.post("/link/ack")
def ack_link(body: dict) -> dict:
    session_id = body.get("sessionId") if isinstance(body, dict) else None
    if not isinstance(session_id, str) or not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required")
    links.clear_link(session_id)
    return {"ok": True}


@router.post("/links")
def list_links(body: dict) -> dict:
    """Pending links whose session has not reached the target cwd yet (already-moved ones are cleared)."""
    from hermes_workstreams.inject import stored_session_cwd
    pending = []
    for link in links.all_pending():
        if stored_session_cwd(link["sessionId"]) == link["cwd"]:
            links.clear_link(link["sessionId"])
        else:
            pending.append(link)
    return {"links": pending}


@router.post("/focus/save")
def save_focus(body: dict) -> dict:
    workstream = _resolve(body)
    if workstream is None:
        raise HTTPException(status_code=404, detail="No workstream for this session")
    content, mtime = body.get("content"), body.get("mtimeNs")
    if not isinstance(content, str) or len(content) > 64_000:
        raise HTTPException(status_code=400, detail="content must be a string under 64 KB")
    if not isinstance(mtime, (str, int)):
        raise HTTPException(status_code=400, detail="mtimeNs is required")
    try:
        core.save_focus(workstream, content, int(mtime))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="mtimeNs is required") from exc
    except core.FocusConflict as exc:
        raise HTTPException(status_code=409, detail="FOCUS.md changed; reload") from exc
    return _payload(workstream)


@router.post("/focus/toggle")
def toggle_focus_task(body: dict) -> dict:
    workstream = _resolve(body)
    if workstream is None:
        raise HTTPException(status_code=404, detail="No workstream for this cwd")
    try:
        line, checked, mtime = int(body["line"]), bool(body["checked"]), int(body["mtimeNs"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="line, checked and mtimeNs are required") from exc
    try:
        core.toggle_task(workstream, line, checked, mtime)
    except core.FocusConflict as exc:
        raise HTTPException(status_code=409, detail="FOCUS.md changed; reload") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="FOCUS.md is missing") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _payload(workstream)
