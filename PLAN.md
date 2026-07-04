# PLAN.md — Mixtape Bug Hunt (working plan)

> Working doc, not a graded deliverable. The graded deliverable is `submission.md`.
> Scope: **all 5 bugs + 1 regression test** (full stretch, +3). Coaching mode: *guide, don't reveal* — Claude explains code and traces call chains; I find and confirm each root cause myself.
> Deadline: **Mon Jul 6, 2:59 AM EDT.**

## Scoring map (why the phases are shaped this way)

| Rubric category | Pts | Phase |
|---|---|---|
| Codebase Map | 3 | 1 |
| Bug Fix Completeness (3+ full RCA entries) | 4 | 3 |
| Root Cause Quality (specific mechanism) | 5 | 3 |
| Navigation Strategy (real path, not lucky guess) | 4 | 2–3 |
| Side-Effect Check (deliberate, specific) | 3 | 3 |
| Commit History (1 commit/fix, `fix:` format) | 3 | 3 |
| AI Usage (specific, honest collaboration) | 3 | 4 |
| **Stretch:** 4th bug / all 5 / regression test | +3 | 3 |

**12 of 25 points reward *how you found it*, not *that you fixed it*.** Reproduce and take notes before changing code.

---

## Phase 0 — Setup (~15 min)
- [x] `git checkout -b bugfix/mixtape`
- [ ] `source .venv/Scripts/activate` → `pip install -r requirements.txt` → `python seed_data.py`
- [ ] Run: `FLASK_APP=app:create_app flask run` (NEVER `python app.py`)
- [ ] Confirm `http://127.0.0.1:5000` responds
- [ ] `pytest tests/` — capture the baseline (which pass/fail before any fix)

## Phase 1 — Orient & Codebase Map (~45 min) → 3 pts
- [ ] Create `submission.md`
- [ ] Read `README.md`, then each service file (ask Claude to explain modules/call chains)
- [ ] Write **codebase map** in `submission.md` BEFORE opening any issue:
  - [ ] Every main file + its *role* (not just its name)
  - [ ] One real data-flow trace, end to end, in my own words
  - [ ] The organizing pattern (routes parse/format → services = logic → models = schema)
- [ ] Read all 5 issue descriptions before picking an order

## Phase 2 — Reproduce (all 5) (~45 min) → feeds Navigation (4 pts)
For each bug: trigger the broken behavior deliberately, write the "how I reproduced it" field. **No code changes yet.**
- [ ] #1 Streak resets — set up the Sunday-boundary condition
- [ ] #2 "Friends Listening Now" shows yesterday's people — recency threshold
- [ ] #3 Same song twice in search — find the multi-tag condition that triggers the 2nd path
- [ ] #4 No notification on rating — reproduce rate-a-song vs add-to-playlist
- [ ] #5 Last playlist song missing — off-by-one / boundary in ordering
Tools: `flask shell` (query seed data), isolate service fns in a REPL, add temp `print()` (remove before commit).

## Phase 3 — Investigate → fix → document → commit (one bug at a time) → 15 pts (+stretch)
**Finish a bug's RCA entry and commit before starting the next.** For EACH bug:
1. [ ] Trace route → service → calls; note files opened + what led me to the line (Navigation field)
2. [ ] Verify diagnosis by running with specific inputs BEFORE fixing
3. [ ] Smallest targeted fix (no unrelated refactors)
4. [ ] Side-effect check — look at the OTHER side of the boundary / related path; re-run `pytest tests/`
5. [ ] Write RCA entry (5 fields: issue#/title · reproduction · navigation · root cause · fix + side-effect)
6. [ ] Commit, conventional format, one per bug: `fix: <specific what-was-wrong>`

Bug checklist (commit per row):
- [ ] #1 streak_service.py — `fix: ...`
- [ ] #2 feed_service.py — `fix: ...`
- [ ] #3 search_service.py — `fix: ...`
- [ ] #4 notification_service.py — `fix: ...`
- [ ] #5 playlist_service.py — `fix: ...`

**Regression test (+1):**
- [ ] Add a test that FAILS against the buggy code (model it on existing `tests/`), for #1 or #3
- [ ] Reference it in `submission.md`: what behavior it verifies + why it would have failed before the fix
- [ ] `test:` commit

## Phase 4 — Final review & AI Usage (~30 min) → 3 pts
- [ ] `git log --oneline` on `bugfix/mixtape` → screenshot; confirm ≥5 separate `fix:` commits (+ `test:`)
- [ ] Re-read each RCA entry: all 5 fields, understandable by a grader who never saw the code
- [ ] Write **AI Usage** section at top of `submission.md`: specific asks, what they clarified, and ≥1 moment I verified/course-corrected the AI

---

## Coaching contract (per CLAUDE.md)
Claude's role: explain what functions do, trace call chains, surface edge cases, compare two code paths.
My role: find each root cause, confirm it by reading/running, author all reasoning in my own words.
Good AI uses to log for the AI Usage section: file/module summaries, data-flow traces, `weekday()` vs `isoweekday()`-style clarifications, "structural diff between these two blocks."
