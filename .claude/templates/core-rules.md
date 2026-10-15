---
id: core-rules
scope: global
order: 10
---

## Core rules

- Prefer the smallest *correct* change (see Change Sizing).
- Preserve existing structure, naming, and patterns. Follow the local style of
  any file you touch.
- No unrelated refactors, formatting passes, or file moves, and do not revert
  unrelated changes.
- Read the relevant files fully before editing them.
- New behavior should be backward-compatible and default-off where practical;
  optional features must fail gracefully rather than break the primary path.
- No large abstractions unless they clearly pay for themselves.
