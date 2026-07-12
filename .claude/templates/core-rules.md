---
id: core-rules
scope: global
order: 10
---

## Core rules

- Prefer the smallest *correct* change — the smallest diff that is actually
  right, not merely the smallest diff. See Change Sizing for when correctness
  requires a larger change.
- Preserve existing structure, naming, and patterns. Follow the local style of
  any file you touch.
- Do not perform unrelated refactors, formatting passes, or file moves.
- Read the relevant files fully before editing them.
- When starting work in a repo, read its `CLAUDE.md` (or `AGENTS.md`) first,
  then load only the files relevant to the task.
- New behavior should be backward-compatible and default-off where practical;
  optional features must fail gracefully rather than break the primary path.
- Do not claim tests, builds, or commands passed unless they were actually run
  and exited 0.
- Do not introduce destructive git operations, and do not revert unrelated
  changes.
- Be pragmatic and direct. No fluff or ceremony, and no large abstractions
  unless they clearly pay for themselves.
