---
description: Validate the most recently completed refactor phase against its Definition of Done (runs tests)
---

# /refactor-checkpoint

Validate that the most recently completed phase satisfies its Definition of Done before
the refactor advances. Run this after every phase, before the next `/refactor-next`.

---

## What to do

### 1 — Identify the phase being validated

Read `.local/REFACTOR.md` `## Session Log`.

Find the most recent row. Note: phase number + name, model used, Complete or Partial.

If the most recent row is `Partial`: report "Most recent phase is partial — checkpoint
cannot run until the phase is fully complete. Finish the phase first." Stop.

If no session log rows exist: report "No completed phases found in the session log." Stop.

### 2 — Run tests

Read `.local/REFACTOR.md` `## Test Command`. Run it exactly as written.

If tests fail:

- Report which tests failed and the relevant output.
- Mark the checkpoint **FAILED — tests**.
- Stop. Do not proceed to remaining checks.

### 3 — Check each Definition of Done criterion

Read the phase's `### Definition of Done` checklist from `.local/REFACTOR.md`.
For each checklist item, assess PASS or FAIL with a brief note.

Then check these structural criteria regardless of the phase:

**Code quality** — Read the files listed in the session log entry. Is the code clean and
consistent with `AGENTS.md` standards? Any obvious hacks or untracked workarounds? FAIL
if yes.

**Technical debt** — Any `// TODO` or `// FIXME` markers introduced by this phase? If
so, are they explicitly tracked in the session log or a follow-up phase? Untracked = FAIL.

**Documentation** — Based on what changed, assess whether any of these needed updating:
`README.md` (flags or env vars), `AGENTS.md` (architecture contracts), `doc.go` in
affected packages, `docs/openapi.yaml` (API behavior). FAIL if a relevant doc was skipped.

**Test coverage** — Were new or updated tests added for changed logic? If behavior changed
and no tests were touched, report WARN (not FAIL — existing coverage may be sufficient,
but flag it).

**ADRs** — If any phase DoD item explicitly requires an ADR, verify the file exists in
`docs/decisions/`. FAIL if required and missing. N/A if not required.

### 4 — Report

Print the checkpoint report:

```text
═══════════════════════════════════════
 Checkpoint — Phase N — [name]
═══════════════════════════════════════
 Tests            PASS / FAIL
 Code quality     PASS / FAIL — [note]
 Technical debt   PASS / FAIL — [note]
 Documentation    PASS / FAIL — [list]
 Test coverage    PASS / WARN — [note]
 ADRs             PASS / FAIL / N/A
 DoD checklist    PASS / FAIL — [N of M items met]
───────────────────────────────────────
 Overall:  PASS — phase is complete
        or FAIL — [N] criteria not met; do not advance
        or WARN — phase can advance, but review [items]
═══════════════════════════════════════
```

On FAIL: list exactly what must be fixed. Do not mark the phase complete.

On WARN: the phase can advance; call out what to revisit later.

On PASS: confirm the phase checkbox in `### Step Index` and the Phase Map row are both
marked `Complete` in `.local/REFACTOR.md`. If either was missed, update it now.
Then tell the user to run `/refactor-next` for the next phase.
