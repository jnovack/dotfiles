---
name: todo-closeout
description: Review and repair the implementation of a completed TODO after it has landed. Use for post-completion verification and fixes; do not use to implement an open TODO or plan follow-on work.
---

# TODO Closeout

Use this workflow after a discrete TODO item has been marked complete and its implementation has landed. This is a closeout review, not a handoff to another item.

## Inputs

- Prefer `TODO=<identifier-or-title>` when the repository has a numbered or named TODO.
- Accept a path, issue or pull-request reference, commit, checklist entry, or quoted TODO text when that is the canonical identifier.
- If `TODO` is omitted, infer the most recently completed item from repository guidance, task or plan files, session logs, commits, and current changes. Ask one concise question only if multiple candidates remain.
- Locate the authoritative TODO record from repository guidance and the supplied identifier. Do not assume a repository-specific tracker or path. Ask if plausible records conflict.

## Fail-closed completion gate

Run this gate before reviewing code, editing files, or changing bookkeeping:

1. Read the authoritative TODO, including its acceptance criteria, discussion, linked changes, and completion status when available.
2. Require the item to be explicitly marked closed or complete. A merged change or nearby implementation is not enough when the authoritative record still says open.
3. Require the implementation claimed by the TODO to be present in the working tree or baseline. Cross-check linked commits or pull requests, repository history, the working tree, and session bookkeeping as available.
4. Establish a bounded review scope from the TODO's stated outcome and acceptance criteria. If the implementation or scope cannot be identified reliably, the item is not ready for closeout.

If any check fails, stop without modifying implementation, tests, documentation, TODO status, or session bookkeeping. State the mismatch and ask the user to identify a completed TODO or finish it through the repository's normal execution workflow. An explicit `TODO` value does not override this gate.

A closeout is never authorization to implement an open item, an unstarted follow-up, or unrelated backlog work. Fixes are in scope only when they repair, complete, or prove the already-landed TODO implementation.

## Review and repair the completed TODO

1. Read applicable repository instructions, including root `CLAUDE.md` when present, and the TODO's requirements, constraints, and definition of done.
2. Establish the implementation baseline from linked changes, commits, the working tree, and task or session bookkeeping. Inspect the actual diff and preserve unrelated user changes.
3. Review the landed code, tests, documentation, migrations or configuration, and bookkeeping for correctness, regressions, security issues, contract or scope violations, lost behavior or comments, missing coverage, and inaccurate completion claims.
4. Fix every in-scope finding directly. Keep repairs tied to the completed TODO; do not broaden the feature, execute follow-on items, or fold opportunistic refactors into the closeout.
5. Add or adjust tests and documentation needed to prove the repaired behavior. Run the narrowest relevant checks first, followed by repository validation appropriate to the risk. Respect authorization gates for live, external, privileged, or destructive actions.
6. Reconcile local checklist or session bookkeeping only when the repaired implementation genuinely satisfies it, and record unavailable validation honestly. Do not reopen, close, comment on, or otherwise mutate an external tracker unless the user explicitly requests that action.

Do not commit, stash, reset, discard, or delete user work unless the user explicitly requests it.

## No handoff

Do not identify, audit, rewrite, or execute the next TODO merely because one exists. Report newly discovered work separately only when it is not required to make the completed item's implementation correct.

## Final response

Report separately:

- the completed TODO and implementation baseline reviewed;
- findings and fixes;
- validation performed and its results;
- confirmation that no follow-on TODO was executed;
- blockers, unavailable validation, or residual risks.

Use evidence-backed file and line references where they help the user verify the work.
