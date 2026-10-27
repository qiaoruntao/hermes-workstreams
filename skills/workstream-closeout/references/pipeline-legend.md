# Pipeline legend

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
