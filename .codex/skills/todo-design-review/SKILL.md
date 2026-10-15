---
name: todo-design-review
description: Review and tighten a TODO's specification interactively, then correct its implementation plan against the spec and current code before implementation. Edit only specification and plan files; do not implement the TODO or repair source code.
---

# TODO Design Review

Prepare a TODO for another agent to implement. Deliver a coherent specification
and an executable implementation plan grounded in the actual project.

## Scope and boundaries

- Do the review yourself. Do not spawn subagents or delegate work.
- Write only the selected TODO's specification and implementation plan files,
  including their existing embedded checklists or review notes. Create a missing
  spec or plan only when the authoritative requirements support it; do not invent
  product intent to fill a gap.
- Read source, tests, configuration, documentation, and history as evidence.
  Do not modify them, execute implementation steps, generate code, install
  dependencies, or run migrations or deployments.
- Resolve code findings through concrete corrections to the spec or future plan,
  never through source patches. Keep unrelated project findings separate in the
  final response rather than expanding this TODO.
- Preserve unrelated edits. Do not change tracker status, move or archive files,
  mark implementation steps complete, or commit, stash, reset, or discard work.

## Find the TODO and its intent

1. Read applicable repository guidance, including root `CLAUDE.md` when present.
2. Prefer `TODO=<identifier-or-title>`. Locate the record in `TODO.md`, or
   `.local/TODO.md` when that is the repository's tracker. Follow repository
   guidance if it names another authoritative location. If no identifier was
   supplied, use a clearly selected item from the conversation; otherwise ask
   which item to review rather than choosing an arbitrary open TODO.
3. Follow the record's links and inspect matching files under `.local/todos/`,
   including nested item directories. Read the full spec, plan, and named design,
   requirements, discussion, or similar supporting files. Names such as `SPEC.md`
   and `PLAN.md` are examples, not required filenames. Distinguish authoritative
   documents from superseded drafts or completed-item archives.
4. Establish the goal, intended users, motivation, scope, non-goals, acceptance
   criteria, known decisions, and current implementation baseline. Inspect the
   working tree so existing behavior and user changes are understood.
5. Resolve conflicting records or missing intent with the user before dependent
   edits. If the item is already implemented or complete, explain that this is a
   pre-implementation workflow and ask for the intended planning target; do not
   turn the review into implementation closeout.

## Pass 1: interactive specification review

Evaluate whether the proposed behavior solves the stated problem and fits the
project. Check assumptions against current code, contracts, repository rules, and
relevant design decisions. Distinguish verified facts, user decisions, and
unresolved assumptions.

Cover what matters for this TODO: observable behavior and examples, interfaces
and data ownership, defaults, edge cases and failure behavior, security and
privacy, concurrency and lifecycle, performance and scale, migration or
operational effects, and testable acceptance criteria. Challenge unnecessary
complexity, duplicated mechanisms, unsafe defaults, and approaches that conflict
with the project's architecture. Explain concrete pitfalls and tradeoffs rather
than adding generic review checklists to the spec.

Ask focused questions when an answer changes behavior, scope, architecture, or
acceptance criteria. Offer a recommendation and meaningful alternatives when
useful. Batch closely related questions, continue independent review, and iterate
as needed. Do not treat silence as a decision or silently choose a consequential
product requirement. Resolve routine technical details from evidence without
asking the user to approve every edit.

Tighten the spec in place. Preserve agreed intent and record material decisions,
their reasons, non-goals, constraints, and observable acceptance criteria where
the implementer will read them. Keep supporting documents read-only; reconcile
their relevant conclusions in the canonical spec and flag any remaining conflict.

Proceed to the plan review when the spec is internally consistent, feasible, and
has no unresolved decision that materially affects implementation. User sign-off
is not a separate required ceremony. If a necessary answer is still pending,
retain the explicit open question and do not claim the design is ready.

## Pass 2: autonomous plan and project review

Use the tightened spec as the behavioral authority and the current working tree
as the implementation baseline. Complete this pass without routine questions.
If a finding requires a major change to agreed behavior, scope, architecture, or
an external contract, explain the impact and return to specification discussion
before revising the dependent plan. Do not silently rewrite the goal to fit an
easier implementation.

1. Review the concept in the context of the project: architecture, existing
   abstractions, ownership and lifecycle, integration paths, maintainability,
   security, performance, and operational costs. Inspect relevant source, tests,
   contracts, callers, and equivalent entrypoints beyond the plan's file list
   when needed to expose missing impact. This is a project-level assessment of
   the TODO, not an unbounded audit of unrelated code.
2. Verify planned files, symbols, dependencies, versions and APIs, ordering,
   prerequisites, and current behavior against evidence. Separate existing
   defects from intended behavior changes; avoid plans that recreate capabilities
   already present or rely on an imagined baseline.
3. Repair every in-scope design or code finding in the plan. Give the implementer
   the concrete defect, affected location, required behavior or repair, and
   appropriate regression validation. Label existing defects as future repairs;
   never imply that the code was fixed during this review.
4. Correct the canonical plan in place: bounded scope, affected files and
   equivalent paths, ordered implementation steps, dependencies, interface and
   data changes, removals, documentation and configuration updates, operational
   implications, and completion criteria. Right-size detail to remove material
   ambiguity without prescribing incidental code structure.
5. Map every acceptance criterion to implementation steps and meaningful
   validation. Include applicable negative cases and cross-component contracts,
   exact validation commands when known, required fixtures or environments, and
   authorization prerequisites for live or destructive checks. Distinguish
   checks run during review from checks the implementer must run later.
6. Re-read the final spec and plan together. Resolve contradictions, stale
   alternatives, omitted requirements, out-of-scope steps, and unsupported
   assumptions. Keep implementation status unchanged and future steps unchecked.

Use non-mutating checks when they resolve a planning uncertainty. Do not run the
implementation's entire validation suite merely to review documents, and do not
claim future checks passed. Record material limits or unavailable evidence in the
spec or plan so the next agent does not inherit false certainty.

## Handoff

Report concisely:

- the TODO and canonical spec/plan reviewed, with links;
- specification decisions and corrections;
- plan corrections, including code findings captured as future repairs;
- checks actually performed and their results;
- readiness for implementation, unresolved questions, and residual risks;
- confirmation that only spec/plan files changed, no agents were spawned, and no
  implementation was executed.

If material questions remain, say the handoff is not ready and identify exactly
what must be resolved. Otherwise hand back the corrected artifacts for the next
agent; do not offer or start implementation as part of this workflow.
