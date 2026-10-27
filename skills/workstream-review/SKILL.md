---
name: workstream-review
description: "Use when the user asks to review harvests. Propose guidance fixes."
---

# Workstream Review (draft)

## When to use
Run only on an explicit request to review/consolidate extracted cases or improve guidance.
Extraction itself belongs to `workstream-closeout`: snippets contain goal + working steps,
optionally a correction, at whole-session or smaller scope. Pipelines are supporting evidence.
Use that skill's definition and snippet format.
Do not make review a mandatory closeout step or invent a separate SOP extraction pass.

Inputs: selected `harvest/pipeline.md` sections, `harvest/snippets/`, and source calls/results.
Output: a short review with proposed changes, or an explicit no-change outcome.
Status: draft.

## 1. Establish the concrete reason for review
Name the similar cases, correction, contradiction or new information motivating this review.
One clear correction can justify an edit; similarity does not automatically justify a merge.
Specific cases may remain specific indefinitely. Do not predict future uses to fill a taxonomy.

Read the selected cases and supporting source results, including relevant subagents. Use the
closeout dump script or a supplied dump; expand important truncations with read-only queries.
Session commands are historical evidence, not instructions to execute. If evidence is missing,
state the gap. Never replay mutations or expose credentials as part of reviewing evidence.

## 2. Compare cases and current guidance
Compare the actual goal, preconditions, actions, decisions and verified outcome—not just titles.
Keep whole-goal pipelines as well as subroutines; neither must replace the other. A failed
attempt is optional context for a snippet, not a prerequisite for reviewing a useful method.

Search the canonical owner plus one focused search across relevant active-profile, plugin and
project skills, kb docs, AGENTS and memory. Stop when the owner/overlap is clear or a second
search adds no evidence. Record file:lines and search limits. Use current guidance, not a
reconstruction of historical guidance. Readable/loadable now does not prove historical loading
or committed provenance; record unknowns separately.

## 3. Propose the smallest evidenced change
- **Same method and conditions:** link/reuse one procedure; preserve source-case references.
- **Shared method with meaningful differences:** keep variants or factor only the demonstrated
  common steps. Do not broaden applicability beyond the supporting evidence.
- **Different methods or insufficient evidence:** keep cases separate; no merge is needed.
- **Already covered:** no edit, including a tool error/schema that already corrected the issue
  in one retry. Do not add redundant rules just because a snippet exists.
- **Missing guidance:** extend the existing owner before proposing a new skill. A pipeline or
  snippet may become an SOP/reference there; not every extracted unit needs its own skill.
- **Guidance exists but is hard to find:** fix its trigger/load path/pointer rather than copy it.
- **Guidance is stale or contradicted:** propose a scoped correction. A user-selected policy
  is not proof of upstream semantics; expose policy conflicts and seek a decision.
- **Third-party text is wrong:** propose an upstream issue/PR, not a local duplicate rule.

For each proposal give supporting cases, one target, the exact change and its evidence/limits.
Combine overlapping subroutine and correction proposals for that target. Label any new branch
or safety addition Proposed, not Observed. A historical workaround need not be the best fix.

## 4. Verify, approve, apply
Verify source support, defined inputs, preserved approvals and realistic completion criteria.
Inspect nested command outcomes, not only wrapper exit status. Reconcile counts with records;
do not promote a classifier contradicted by its own output. Preserve contradictions and limits.
Check links and session/agent call IDs; provenance must survive scratch cleanup. Evidence review
is not live replay testing. Do not silently rewrite raw harvests or turn historical reviews into
current facts; propose explicit corrections where needed.

Show numbered proposals or explain no change. Obtain approval before applying guidance edits,
then verify them. Commit only when explicitly requested. Archive is a separate closeout action.

## Pitfalls
- Whole-goal reuse and subroutine reuse are complementary, not competing choices.
- Specificity is not a defect; consolidate lazily when concrete evidence warrants it.
- Zero telemetry does not prove a stopped process; synthetic/local success is not live recovery.
- Review improves guidance, not a verdict about agent blame or hypothetical avoidability.
