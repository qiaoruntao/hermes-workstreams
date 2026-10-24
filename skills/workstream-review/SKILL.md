---
name: workstream-review
description: "Use when the user asks to review harvested snippets. Turn them into skill/doc edits."
---

# Workstream Review (draft)

Run only on an explicit user request, after `workstream-closeout` produced `harvest/snippets/`.
Input: snippets (raw, evidence-backed). Output: proposed edits to the current guidance.
Purpose: make the **current** skills and docs better. Not to decide whether the agent was to
blame: an agent can miss written guidance for many reasons (long context, recall missed it,
the skill was not triggered), so "avoidable" is not judged.

Status: outline. Steps are added only after a trial on real snippets shows they are needed.

## 1. Find current guidance per snippet
For each snippet, search the current skills (`~/.hermes/skills`, plugin and project skills),
kb docs, AGENTS.md and memory for its Trigger and its Right side. Record what exists (path + the
lines), or "none". Use the guidance as it is now; never reconstruct what existed at session time.

Also check that the guidance found is committed and loadable by the agent that failed (a kb
skill symlinked only for Claude/Codex never reaches Hermes; an uncommitted doc can be lost).

## 2. Propose one edit per snippet
Pick the smallest change that would make the Right step the obvious first move next time:
- **already corrected** (the tool's own error/schema states the fix and the agent recovered
  in one retry) → no edit.
- **none exists** → add the rule where the task's guidance lives (extend a skill before creating one).
- **exists but did not reach the agent** → fix how it is found (load path, skill trigger, a
  pointer from where the agent looked first); never copy it a second time.
- **exists and is wrong or stale** → fix it in place; the session's evidence beats the doc.
- **third-party text is wrong** (tool schema, bundled skill) → an upstream issue/PR.
Each proposal names one target file and the exact text change, and cites the snippet. A
snippet's Right may be a workaround; propose the better fix if the error text names it.

## 3. User approval, then apply
Show all proposals as a numbered list; the user approves per item. Apply approved edits,
then commit the changed guidance together with the snippets it came from.

## Pitfalls
- One snippet is weak evidence; note when several snippets point at the same edit.
