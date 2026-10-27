# Model agreement test (evaluates the skill, not a closeout step)

Purpose: after editing the legend or rules, check that models other than the author mark the
same sessions the same way. Steps where models split show wording that is still ambiguous.

Harness (local, not in this repo): a `model-agreement/` dir with two scripts:
- `run.py <session_ids,comma> <models,comma> [tag]`: dumps each session with
  `scripts/dump_session.py`, labels user turns `U<k>`, and asks each model for one marker per
  CALL/U step plus `used_by` for each ★. Writes `out/<model><tag>__<sid>.json`. **Keep its
  prompt in sync with the legend in SKILL.md.**
- `compare.py`: pairwise agreement, the steps where runs disagree, and ★ steps with no
  consumer or a non-★ consumer. Compares against `reference.json` (our hand-drawn trees mapped
  to CALL ids). Writes `report.md`.

Models that work headless from the Mac:
- GPT-5.6 (Hermes default): `hermes chat --oneshot -Q --ignore-rules -t todo --source tool --query-file <f>`
- Sonnet / Haiku: `claude -p --model sonnet|haiku --tools "" --no-session-persistence --output-format json`
- Not usable: GLM-5.3 on NVIDIA NIM (timed out >15 min); `codex` (refresh token expired);
  `gemini` (account not eligible).

Method:
- Use two short sessions with failures and user turns. Run Sonnet twice to measure run-to-run
  noise; cross-model agreement close to that number means the wording is clear.
- Read the disagreeing steps, not just the percentages. A cluster of the same kind of step
  means a rule is missing; scattered splits are noise.
- Models get only the legend, not the pitfalls, so the test checks the legend's wording.

Record results next to the harness, one report per legend version.
