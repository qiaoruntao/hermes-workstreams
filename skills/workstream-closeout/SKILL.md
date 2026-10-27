---
name: workstream-closeout
description: "Use when harvesting sessions or closing out workstreams."
---

# Workstream Closeout (draft)

Run only on an explicit user request. Never suggest it.
- **Close out** a workstream ("close out <slug>", `/workstream close`): phases **1 Assess → 2 Harvest → 3 Archive**.
- **Harvest only** (any session, no workstream needed): phase 2 alone; ask where to write the output.

Stop for user approval after each phase. Status: phase 2 is being defined; phases 1 and 3 are outlines.

## Core definitions
The **pipeline** is the session record: what happened, in order, with its findings.

A **snippet** is a set of facts about one goal: which calls work for it, what each shows,
and which calls fail. It is smaller than its pipeline lines and adds nothing new to them.
It is not a procedure: the agent using it decides what to run, skip, and in what order.
Ordering between goals stays in the pipeline. A snippet is not automatically a skill.

The acceptance test: an agent given only the goal and the snippet makes a correct call on
its first try and none of the listed wrong ones.

## 1. Assess
Read `FOCUS.md`, `backlog.md`, notes, and `git status` of listed repos. Report: done / not done
(open items). Every open item must be marked done, dropped (reason), moved, or upstream before phase 2.

## 2. Harvest — raw extraction only
Purpose: record the session as a pipeline, then extract goal + right/wrong-call snippets.
Outputs go in a new `harvest/` dir inside the workstream (or the dir the user names). Never
edit the workstream's existing files (FOCUS, notes, handoff); commit them as they are first.
```
<workstream>/harvest/
├── <date>-<title-slug>.md   one per session: pipeline section + extraction report
└── snippets/<slug>.txt      one goal each: correct and wrong calls as facts
```
`<date>` is the session start (YYYY-MM-DD); `<title-slug>` is the session's generated title
(`sessions.title`), lowercased, hyphenated, ≤ 60 chars. The session id goes inside the file.
One clean subagent per session can extract in parallel; each writes only its own session file.
Never write a credential into the harvest: mask it (`***`) and check with a grep before commit.
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

### 2.3 Write the session file
The session file `<date>-<title-slug>.md` holds:
````
# <session title>
`<id>` · <date> · Legend: workstream-closeout `references/pipeline-legend.md` @ <plugin commit>
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
- A ★ result names the value that drove the next step, not just a count: `list services →
  no gphoto-upload; uploader is gphotos-drop → E4`. A ↻★ also names what changed from its ✗.
- **Where** in each ★ path step: the host and how to reach it (`rp5 (ssh raspberrypi5@rp5.lan)`,
  `mac (admin)`), a tool server (`SigNoz MCP`), or `user`.

**Legend**: markers ★ ✗ · ? ↻ ×N are defined in `references/pipeline-legend.md`. Read it
before marking; pipeline files cite it instead of copying it.

**Check the ★ steps** before writing the ★ path. When the ★ steps form more than one branch
(parallel checks, subagents), end each branch's last ★ line with what used it, by tree label:
`→ E4`, `→ A1 E2`, `→ Outcome`. A ★ that nothing later used is not ★. A single pass needs no
labels.

### 2.4 Extract snippets
Work from the finished pipeline. One snippet per goal; every snippet uses the format below.
- **Episode goal:** each E with a ★. Goal = the E's sub-goal, with the session's real names.
  An E with no ★ gets no snippet. Its ✗ calls go to the snippet of an E whose ★ reached the
  same goal; otherwise they are dropped.
- **Generic goal:** a ✗ that would fail the same way in any task (e.g. shell quoting). Goal is
  written without the task's names. Needs a working way to the same goal in the session;
  without one, no snippet. If a snippet with the same goal already exists in this session,
  add a line to it. Do not dedupe across sessions; merging is `workstream-review`'s job.

**Which ✗ become `no` lines.** Record a ✗ only when its result does not show the fix: the
result misleads (empty, zero rows, a count that looks fine, apparent success) or the fix
needs a fact the error does not give (which account, which PATH). Skip errors that name
their own fix (unknown tool name, bad or missing argument, typo, schema error).

**Which lines are worth keeping.** A line (`ok` or `no`) stays only if it passes one of:
- it failed in a way that hides the fix (the `no` rule above);
- it holds something an agent could not guess: an exact name, account, path, filter, ID
  mapping or command shape that is not in the tool schema or obvious docs;
- it was costly to find: several attempts, a long run, or a risky action.
Drop the rest: calls that worked first time, are cheap to redo and teach nothing new (read a
known doc, `df -h`, `pm2 status` once access works). Drop session-only IDs (PIDs, question
text, delegation goals) and how a code fix was applied. A snippet left with no line is not
written; list the E as skipped in the report.

A snippet contains only facts:
- `ok` — a ★ call. Its `→` line names the kind of information it shows (`sweep summaries`,
  `log paths`), never the session's findings (`43 files`, `errors=1 at 15:01Z`); those stay
  in the pipeline.
- `no` — a ✗ call with the same goal. Keep only the part that caused the failure; add a short
  `(cause)` only if it is not obvious. Its `→` line is the error, or for a misleading result
  the output and what contradicted it (`prints 0 while the log has "upload failed file="
  lines`); no other values. Wrong calls with the same result share a line, joined by `|`.
- `needs` — another snippet whose fact a call depends on (login, PATH). Drop that part (the
  ssh/PATH prefix) from this snippet's calls.

Rules:
- Facts are unordered. No steps, reasons, branches, gates, limits or findings.
- Add nothing that is not on the E's pipeline lines or in their calls and results.
- Take calls from the full tool call in `state.db` (the dump can truncate and double escapes).
- Trim, never replace. Drop wrappers and arguments that are obvious or a default (tool_call
  wrapper, free-text context, limits, timeouts, print headers); keep every part that is the
  lesson (account, PATH, exact name, filter). Never swap a command for a different one, even
  an equivalent one. A call that bundles several commands may be split into one `ok` line per
  command whose result was used; drop commands a result showed broken.

Template, `snippets/<slug>.txt` (keywords start the line; continuation lines are indented):
```
goal    <one line>
needs   <other snippet slug>                     (optional)
source  <session file name> · E<k> [E<k>] · CALL#a b c

ok  <call>
    → <what it shows>

no  <failing part>   |   <another with the same result>   (<cause>, optional)
    → <error or misleading output>
```

### 2.5 Verify extraction
- Every E with a ★ has a snippet, its facts are in another snippet with the same goal, or it
  is listed as skipped by the keep rule.
- Every `ok` comes from a ★ call and every `no` from a ✗ call cited in `source`; each call
  is the `state.db` call, only trimmed or split as 2.4 allows.
- Every ✗ whose result misleads or hides its fix is a `no` somewhere, or its E has no ★.
- No snippet holds a finding, step order, or text that is not in its pipeline lines.
End the session file with `## Extraction report`: snippets made, ✗ and E's skipped (with the
rule), rules hard to apply. Do not run the recorded commands, merge across sessions or update
skills as part of extraction.

## 3. Archive
After the user approves the harvest:
1. Commit the workstream dir (FOCUS, notes, `harvest/`) so snippets stay replayable.
2. Open work that stays unfinished stays in the workstream files (e.g. `handoff.md` as the
   resume point); say so in the report. Do not move it into project files without approval.
3. `hermes sessions archive --cwd <dir> --include-open --dry-run` → show the list → same with
   `--yes`. Without `--include-open`, sessions never formally ended are silently skipped.
   Archiving hides sessions; nothing is deleted.
4. Confirm none are left: rerun the dry run → "No sessions match".
5. Only then `hermes project archive <slug>` (restorable with `hermes project restore`).
Archive the current session last, if it belongs to the workstream.
Consolidating pipelines/snippets into revised procedures and skill/doc edits belongs to
`workstream-review` (draft), run on request after the harvest. Evidence stays traceable.

## Pitfalls
- Summaries hide errors, e.g. a query that used the user's informal service name instead of the real one.
- Record calls as made (wrong names, hardcoded versions); fixing them is a later phase.
- If one pattern returned 0 and a looser one returned N, check the result line before you mark it ★.

## Evaluating this skill (not part of a closeout)
After changing the legend or rules, check that different models still mark the same sessions
the same way: `references/model-agreement.md`. Steps where models split point at wording to fix.
For a requested usefulness trial, give clean agents only the task and snippets, not the source
or failure ledger. Compare their next actions against source mistakes; fix gaps and retest with
fresh agents. Preserve the baseline, check command syntax, and report blocked/unexercised cases
separately from prevented mistakes. An offline plan test is not live execution proof.
For critical conditional guards, also give clean consumers the recorded error response and
check their next action. Merely mentioning an untriggered safeguard is not a passed branch test.
