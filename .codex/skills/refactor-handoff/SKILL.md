---
name: refactor-handoff
description: Audit and repair a phased refactor's plan before its first phase, review and repair a completed phase plus the next phase's plan between phases, or perform a final review after its last phase. Never execute an unstarted or partial phase.
---

# Refactor Handoff

Use this workflow at a phased refactor's boundaries: before implementation,
between completed and unstarted phases, or after the final phase.

## Inputs and boundary selection

- Locate the canonical refactor plan using repository guidance and obvious
  plan files, including archived completed plans. Do not assume a
  repository-specific path. Ask if multiple plausible plans conflict.
- Accept `MODE=preflight|handoff|final` when supplied; otherwise infer the
  boundary from the request, phase map, session log and current changes.
- For a between-phase handoff, prefer `PHASE=<number-or-identifier>` for the
  completed phase. Accept `NEXT_PHASE=<number-or-identifier>` when the
  successor is not obvious; otherwise infer the next phase from the plan.
  When `PHASE` is omitted, infer the most recently completed phase.
- With all phases not started, select preflight: audit the first phase's plan
  against the current code and shared constraints, without implementation.
- With all phases complete and no successor, select final: review the final
  phase and the whole refactor's integration against its intent and contracts.
- Ask one concise question only if the intended boundary remains ambiguous.
  Explicit inputs select a boundary; they do not override its status gate.
  Do not silently reinterpret an explicitly requested between-phase handoff
  as final mode because its successor is already complete.

## Fail-closed boundary gate

Run this gate before reviewing code, editing files, or changing bookkeeping:

1. Read the canonical plan's phase map and relevant step/status bookkeeping.
2. Require the statuses for the selected boundary:
   - **Preflight:** all phases and steps are explicitly not started. There is
     no completed phase to review; the first phase is the plan-audit target.
   - **Handoff:** the requested phase and its steps are explicitly complete,
     with its planned implementation present in the working tree or baseline.
     Its successor and successor steps must still be not started.
   - **Final:** all phases and steps are explicitly complete, their planned
     implementation is present in the working tree or baseline, and the plan
     has no successor phase. An archived plan is a valid final-review target;
     do not reopen it merely to record the review.
   If supplied, `PHASE` must identify the completed phase in handoff mode or
   the last phase in final mode; `NEXT_PHASE` must identify the plan-audit
   target in preflight/handoff mode. Preflight has no completed `PHASE`, and
   final mode has no `NEXT_PHASE`.
3. Cross-check the statuses against the working tree, commits and session log.
   A missing implementation is evidence that a phase was not completed, not a
   finding to repair by executing the phase. A partial phase is not a valid
   boundary for any mode.

If any check fails, stop without modifying implementation, tests, plans,
status or session bookkeeping. State the mismatch and ask the user to correct
the mode/phase inputs or run the repository's phase-execution workflow.

A boundary review never authorizes execution of an unstarted or partial phase.
"Fix every in-scope finding" below applies only to defects in existing
implementation whose completed-phase gate passed. Preflight permits plan and
review-bookkeeping edits only; it does not permit source or test edits.

## Review and repair completed work

Skip this section in preflight mode.

1. Read applicable repository instructions, including root `CLAUDE.md` when
   present, plus the plan's shared constraints, definition of done and relevant
   phases. In final mode, include the whole refactor's intent and contracts.
2. Establish the review baseline from commits, the working tree and
   plan/session bookkeeping. Inspect the actual diff and preserve unrelated
   user changes. In final mode, cover the whole refactor's integration rather
   than reviewing only the final phase's diff.
3. Review implementation, tests, documentation and bookkeeping for correctness,
   regressions, security issues, scope or contract violations, lost behavior
   or comments, missing coverage and inaccurate completion claims.
4. Fix every in-scope finding directly. Do not merely report findings, and do
   not pull unstarted work or unrelated follow-ups into the review.
5. Run the narrowest relevant checks first, followed by phase or repository
   validation appropriate to the risk. Respect authorization gates for live,
   external, privileged or destructive actions.
6. Update reviewed phases' checklists, status and session log only when the
   implementation genuinely satisfies them. Record unavailable validation
   honestly. In final mode, record the final-review outcome in the canonical
   plan, retaining its completed/archive location when still accurate.

Do not commit, stash, reset, discard or delete user work unless the user
explicitly requests it.

## Audit and repair the upcoming phase's plan

Run this section for the first phase in preflight mode or the successor in
handoff mode. Skip it in final mode: no successor is required or invented.

1. Read applicable repository instructions and the plan's shared constraints,
   intent, definition of done and target phase if not already read.
2. Treat the current working tree (including any completed-phase repairs) as
   the target phase's baseline.
3. Verify every target-phase assumption against current code, dependency
   versions and APIs, repository guidance and earlier phases' contracts.
4. Repair the canonical plan in place: dependencies, scope, files, ordered
   steps, tests, behavioral deltas, safety gates, completion criteria and
   session bookkeeping. Remove stale, impossible or contradictory instructions.
5. Keep the target phase and its steps marked not started. Do not implement
   them or mark readiness as completion.
6. Run non-mutating consistency checks for the revised plan and working tree
   where useful.

## Final response

Report the selected boundary and, separately as applicable:

- completed-work findings and fixes (or no implementation review in preflight);
- validation performed and its results;
- first/next-phase plan corrections (or no successor in final mode);
- confirmation that no unstarted or partial phase was executed;
- blockers or residual risks.

Use evidence-backed file and line references where they help verify the work.
