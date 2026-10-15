---
name: refactor-handoff
description: Review and repair the implementation of a just-completed phase in a phased refactor, then audit and repair the next phase's plan without executing that next phase.
---

# Refactor Handoff

Use this workflow after one phase of a phased refactor has been implemented and the next phase is planned.

## Inputs

- Prefer `PHASE=<number-or-identifier>` for the completed phase.
- Accept `NEXT_PHASE=<number-or-identifier>` when the successor is not obvious; otherwise infer the next phase from the canonical plan.
- If `PHASE` is omitted, infer the most recently completed phase from the plan, session log, and current changes. Ask one concise question only if multiple candidates remain.
- Locate the canonical refactor plan using repository guidance and obvious plan files. Do not assume a repository-specific path. Ask if multiple plausible plans conflict.

## Fail-closed phase gate

Run this gate before reviewing code, editing files, or changing bookkeeping:

1. Read the canonical plan's phase map and the requested phase's step/status bookkeeping.
2. Require the requested completed phase to be explicitly marked complete, with its planned implementation present in the working tree or baseline.
3. Require the successor being audited to still be marked not started. If it is already partial or complete, this is not the requested handoff boundary.
4. Cross-check those statuses against the working tree and session log. A missing implementation is evidence that the phase was not completed, not a finding to repair by executing the phase.

If any check fails, stop without modifying implementation, tests, plans, status, or session bookkeeping. State the mismatch and ask the user to correct `PHASE`/`NEXT_PHASE` or run the repository's phase-execution workflow. An explicit `PHASE` value does not override this gate.

A handoff is never authorization to execute an unstarted or partial phase. "Fix every in-scope finding" below applies only to defects in implementation that already exists for a phase which passed this gate.

## Review and repair the completed phase

1. Read applicable repository instructions, including root `CLAUDE.md` when present, plus the plan's shared constraints, definition of done, completed phase, and next phase.
2. Establish the phase baseline from commits, the working tree, and plan/session bookkeeping. Inspect the actual diff and preserve unrelated user changes.
3. Review implementation, tests, documentation, and bookkeeping for correctness, regressions, security issues, scope or contract violations, lost behavior or comments, missing coverage, and inaccurate completion claims.
4. Fix every in-scope finding directly. Do not merely report findings, and do not pull next-phase work into the completed phase.
5. Run the narrowest relevant checks first, followed by the phase or repository validation appropriate to the risk. Respect authorization gates for live, external, privileged, or destructive actions.
6. Update the completed phase's checklist, status, and session log only when the implementation genuinely satisfies them. Record unavailable validation honestly.

Do not commit, stash, reset, discard, or delete user work unless the user explicitly requests it.

## Audit and repair the next-phase plan

1. Treat the repaired working tree as the next phase's baseline.
2. Verify every next-phase assumption against the current code, dependency versions and APIs, repository guidance, and contracts established by earlier phases.
3. Repair the canonical plan in place: dependencies, scope, files, ordered steps, tests, behavioral deltas, safety gates, completion criteria, and session bookkeeping. Remove stale, impossible, or contradictory instructions.
4. Keep the next phase marked not started. Do not implement it.
5. Run non-mutating consistency checks for the revised plan and working tree where useful.

## Final response

Report, separately:

- completed-phase findings and fixes;
- validation performed and its results;
- next-phase plan corrections;
- confirmation that the next phase was not executed;
- blockers or residual risks.

Use evidence-backed file and line references where they help the user verify the work.
