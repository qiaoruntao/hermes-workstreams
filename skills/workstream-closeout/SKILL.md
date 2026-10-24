---
name: workstream-closeout
description: "Use when the user asks to close out a workstream or harvest sessions. Tree + snippets, then archive."
---

# Workstream Closeout (draft)

Run only on an explicit user request. Never suggest it.
- **Close out** a workstream ("close out <slug>", `/workstream close`): phases **1 Assess → 2 Harvest → 3 Archive**.
- **Harvest only** (any session, no workstream needed): phase 2 alone; ask where to write the output.

Stop for user approval after each phase. Status: phase 2 is being defined; phases 1 and 3 are outlines.

## 1. Assess
Read `FOCUS.md`, `backlog.md`, notes, and `git status` of listed repos. Report: done / not done
(open items). Every open item must be marked done, dropped (reason), moved, or upstream before phase 2.

## 2. Harvest — raw extraction only
Purpose: show the correct flow for this kind of task and the correct way to call each tool.
Outputs stay local to the workstream (or the dir the user names):
```
<workstream>/harvest/
├── pipeline.md          legend + one section per session
└── snippets/<slug>.md   one file per snippet
```
Record what happened, nothing more. Add no field, label, or analysis that this skill does not define.

### 2.1 Find sessions
Query `~/.hermes/state.db` read-only; queries in `references/state-db-session-queries.md`.
- Close out: sessions whose `cwd` is the workstream dir.
- Testing the method: a short session (1–4 user turns, 12–40 calls, several failures).
Show the list; the user confirms or adds sessions.

### 2.2 Read a session
`python3 <this skill>/scripts/dump_session.py <session_id> [--width N]` prints one line per
USER / ASSISTANT / CALL#n / RES#n (RES#n answers CALL#n; parallel results arrive out of order),
then each subagent session as `## SUBAGENT A<k>` with lines prefixed `A<k>`. Read the whole
dump, line by line; never draw from a summary.

### 2.3 Write the session section in `pipeline.md`
`pipeline.md` starts with the legend below. Each session section:
````
## S<n> <session title>
`<id>` · <date>
Goal: <one short, accurate sentence>

```
├── E1 <sub-goal>                          ✗
│   ├── ✗  <call, short>                   → <result, short>
│   └── ↻★ <call, short>                   → <result>
├── ★  U2: <what the user asked or decided, rewritten>
└── E2 <sub-goal>
    └── ★  delegate_task: <task>           → <result>
        └── A1 <subagent task>
            └── E1 <sub-goal>
                └── ★  <call, short>       → <result>
```

Outcome: <what the session concluded, with key numbers; what it left unconfirmed>

```
★ path
  1. <where>: <exact command or tool call>
```
````
- **Goal and user turns are rewritten, not quoted.** User messages can be vague or misleading.
  Write what the user wanted in one short sentence, with the real names found in the session.
- **Every later user turn is a step** `U<k>` with a marker, like a call. One line per statement
  when a turn mixes requests and claims. The user can be wrong, so mark by evidence:
  - A request or decision: ★ if the answer needed it, · if not, ✗ if a result showed it was
    based on a wrong premise.
  - A claim about facts (a cause, how a system behaves): ✗ if a result contradicts it, `?` if no
    result checked it, else ★ or · like any step.
  - A user correction makes an agent line ✗ only if it is about intent or a result confirms it.
  - Rows starting `[ASYNC DELEGATION` or similar system notices are not user turns.
- **Subagents** (`## SUBAGENT A<k>` in the dump) are drawn under their `delegate_task` line as
  `A<k> <task>`, with their own episodes and markers.
- **E** = episode: consecutive steps serving one sub-goal. New sub-goal → new E. An E with no ★
  gets ✗ on its line.
- One line per call. A call that ran several commands with different outcomes gets one line per
  command.
- Tree lines are short. Exact commands appear only in the ★ path, in order, including ★ user
  steps (`user: <decision>`) and ★ subagent steps.
- **Where** in each ★ path step: the host and how to reach it (`rp5 (ssh raspberrypi5@rp5.lan)`,
  `mac (admin)`), a tool server (`SigNoz MCP`), or `user`.

**Legend**
- One marker per step:
  - `★` on the shortest correct path: without it the answer cannot be reached or proven. Needs a
    result that worked.
  - `✗` failed, misleading, or contradicted by a result. A failed call stays ✗ even when its
    error showed what to change: it is a learning step, skipped next time; its fix is the `↻★`.
  - `·` worked but not needed for the answer.
  - `?` not verified: a shortcut never tried, or a claim no result checked; never ★ it.
- An empty result (0 rows, not found) is ★ only if the call was right and needed, e.g. it ruled
  out a likely cause the answer depends on. If a later step shows the input was wrong (name,
  pattern, field), it is ✗. A right but unneeded check is ·.
- Optional, before the marker:
  - `↻` changed retry of an earlier ✗ step in the same episode: same intent, different input.
  - `×N` the same call repeated N times, shown once.

**Check the ★ steps** before writing the ★ path. When the ★ steps form more than one branch
(parallel checks, subagents), end each branch's last ★ line with what used it, by tree label:
`→ E4`, `→ A1 E2`, `→ Outcome`. A ★ that nothing later used is not ★. A single pass needs no
labels.

### 2.4 Write snippets
A snippet pairs a ✗ step (Wrong) with a step of the same intent in the same session that worked
(Right), in any episode or subagent. Right must be a tool call whose result in the session
shows it worked. User statements and assistant summaries are never evidence; with no
such result, write no snippet. Template, `snippets/<slug>.md`:
```
# <slug>
Trigger: <the sub-goal, in one line>
Wrong: <where>: <failed call> → <exact error>
Right: <where>: <exact working call>
Evidence: S<n> <CALL#k from the dump> → <the result that shows it worked>
```

## 3. Archive (outline)
After the user approves the harvest: commit the workstream dir (FOCUS, notes, `harvest/`) so
snippets stay replayable; `hermes sessions archive --cwd <dir> --dry-run` → show → `--yes`;
`hermes project archive <slug>`. Archive the current session last.
Turning snippets into skill/doc edits is a separate skill, `workstream-review` (draft), run on
request after the harvest.

## Pitfalls
- Summaries hide errors, e.g. a query that used the user's informal service name instead of the real one.
- Record calls as made (wrong names, hardcoded versions); fixing them is a later phase.
- If one pattern returned 0 and a looser one returned N, check the result line before you mark it ★.

## Evaluating this skill (not part of a closeout)
After changing the legend or rules, check that different models still mark the same sessions
the same way: `references/model-agreement.md`. Steps where models split point at wording to fix.
