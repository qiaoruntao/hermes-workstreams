---
name: workstream-focus
description: "Use when a request starts or continues a multi-session workstream. Link and keep FOCUS.md."
---

# Workstream Focus

A **workstream** is one issue/goal worked across several sessions (e.g. debugging one
incident). Each workstream is a Hermes Project whose **only folder** is
`<workstreams_root>/<slug>/` (default `~/hermes-workstreams/`, setting `workstreams_root`). The plugin shows that
folder's `FOCUS.md` in the Desktop side panel and injects it into the agent context.

## 1. Decide: none, existing, or new
- Quick question / one-off task → do nothing.
- Matches an existing workstream (folder names + their FOCUS.md) → link it.
- A new multi-session issue → create one.
- Unsure → ask the user in one line. Never link silently on a weak match.

## 2. Link or create — use the `workstream_link` tool
- New: `workstream_link(slug=<kebab-case>, create=true, name=…, first_task=…, icon=…)`.
  It creates `<root>/<slug>/`, a starter `FOCUS.md`, and the Hermes Project (only that folder).
  Then edit FOCUS.md to fit the template below.
- Existing: `workstream_link(slug=…, create=false)`.
- The move is **pending** until this turn ends: the Desktop panel then moves the chat into the
  project (same as sidebar **Move to project**). Within this turn use absolute paths; from the
  next turn the cwd and the injected FOCUS.md follow. Tell the user it will link after this reply.
  Outside Desktop (CLI, messaging) nothing moves it — ask the user to use Move to project.
- Do NOT use `desktop_project` or `hermes project create --use` for this: on Desktop gateway
  chats they don't move the chat, and `--use` changes the profile-global active project.
- **Never add code repos as project folders** — project membership is cwd-derived, so every
  unrelated session in that repo would join this project. List repos in FOCUS.md instead.
- One session links one workstream. You may still read/update another workstream by path.

## 3. Load context
Read `FOCUS.md` first. Read other files in the dir only when the task needs them.
Before working in a linked repo, read its `AGENTS.md` (and list its project skills): the
session cwd is the workstream dir, so repo context does NOT auto-load.

## 4. FOCUS.md rules — every word counts
It is what the user reads to grasp the situation in seconds.
- Contains only: what is being done now, what is blocked and on what, the next decision or
  question for the user, the single finding that changes direction, and `Repos:`.
- Budget: ≤ 12 non-empty lines and ≤ 100 words (the panel flags overruns).
- A status line only when tasks cannot express it (`Blocked: …`, `Waiting on user: …`,
  `Deployed, watching …`).
- Done items: tick them; remove them on the next update.
- Everything else goes elsewhere in the dir, any layout (e.g. `backlog.md`, `log.md`,
  `notes/…`). Link a file from FOCUS.md only if it is critical now.

Template:
```markdown
# <short title>
- [ ] <current task>
- [ ] <next task>
Next decision: <question for the user, if any>
Repos: ~/projects/<repo>
```

## 5. Keep it current
Update FOCUS.md at the end of any turn that changed the state (task done, new blocker,
direction change). Prune on every update. Use targeted `patch` edits; the user may tick
boxes in the panel concurrently, so re-read before rewriting the whole file.
