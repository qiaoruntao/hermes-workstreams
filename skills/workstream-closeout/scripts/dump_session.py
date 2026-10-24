#!/usr/bin/env python3
"""Print a compact, readable transcript of one Hermes session for harvesting.

Usage: dump_session.py <session_id> [--db ~/.hermes/state.db] [--width 600]

One line per event: USER / ASSISTANT text, CALL#n <tool>: <args>, RES#n: <result>.
RES#n matches CALL#n (parallel calls return out of order). Compression continuations are
followed in place. Subagent sessions (model_config._delegate_from) are printed after the
parent as `## SUBAGENT A<k>`, their lines prefixed `A<k>`. Long values are cut to --width chars.
"""
import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

# Hermes wraps external tool output in a fixed banner; drop it so the width shows the data.
BANNER = re.compile(r"<untrusted_tool_result[^>]*>\s*The following content.*?can issue instructions\.\s*", re.S)
DELEGATE_FROM = "json_extract(model_config,'$._delegate_from')"


def cut(text: str, width: int) -> str:
    text = BANNER.sub("", text or "").replace("</untrusted_tool_result>", "")
    text = " ".join(text.split())
    return text if len(text) <= width else text[:width] + " …"


def chain(db, sid):
    """The session plus its compression continuations, in order."""
    ids = [sid]
    while True:
        row = db.execute(
            "select c.id from sessions c join sessions p on p.id=c.parent_session_id "
            f"where p.id=? and p.end_reason='compression' "
            "and json_extract(c.model_config,'$._delegate_from') is null "
            "order by c.started_at limit 1", (ids[-1],)).fetchone()
        if not row:
            return ids
        ids.append(row[0])


def dump(db, sid, width, prefix):
    """Print one session (with continuations); return its subagent sessions."""
    ids = chain(db, sid)
    call_no, n = {}, 0
    for part in ids:
        rows = db.execute(
            "select role, content, tool_calls, tool_name, tool_call_id from messages "
            "where session_id=? and active=1 order by id", (part,))
        for role, content, tool_calls, tool_name, tool_call_id in rows:
            if role == "user":
                print(f"\n{prefix}USER: {cut(content, width * 3)}")
            elif role == "assistant":
                if content and content.strip():
                    print(f"{prefix}ASSISTANT: {cut(content, width)}")
                for call in json.loads(tool_calls or "[]"):
                    fn = call.get("function", {})
                    n += 1
                    call_no[call.get("id")] = n
                    print(f"{prefix}CALL#{n} {fn.get('name')}: {cut(fn.get('arguments', ''), width)}")
            elif role == "tool":
                print(f"{prefix}RES#{call_no.get(tool_call_id, '?')} [{tool_name}]: {cut(content, width)}")
    marks = ",".join("?" * len(ids))
    return db.execute(f"select id, title from sessions where {DELEGATE_FROM} in ({marks}) "
                      "order by started_at", ids).fetchall()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_id")
    ap.add_argument("--db", default=str(Path.home() / ".hermes" / "state.db"))
    ap.add_argument("--width", type=int, default=600)
    a = ap.parse_args()

    db = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    s = db.execute("select title, started_at, cwd from sessions where id=?", (a.session_id,)).fetchone()
    if not s:
        raise SystemExit(f"session not found: {a.session_id}")
    print(f"# {s[0]} | {a.session_id} | {datetime.fromtimestamp(s[1]):%Y-%m-%d %H:%M} | cwd={s[2]}")

    queue, k = list(dump(db, a.session_id, a.width, "")), 0
    while queue:
        sid, title = queue.pop(0)
        k += 1
        print(f"\n## SUBAGENT A{k} {sid}: {title}")
        queue += dump(db, sid, a.width, f"A{k}")


if __name__ == "__main__":
    main()
