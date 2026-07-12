---
id: intent-capture
scope: global
requires: [change-sizing, documentation-style]
order: 24
---

## Intent Capture

Record the *why* of an intentional or non-obvious behavior as part of the same change that
introduces it — do not wait to be asked. Claude writes both the code and its tests, so Claude,
not the user, is the producer of intent. This is the producer counterpart to the *Change Sizing*
rule, which can only respect intent that was actually written down.

- **Inline at the code point.** State the failure mode a naive revert or "simplification" would
  cause, not just that the code is intentional (extends the `Documentation` why-rule). A reason
  that sits on the changed lines survives refactors; a record in a distant file does not.
- **Behavior gets a guard test, not prose.** If the intentional thing is observable at runtime,
  add or update a named test whose name states the decision and that fails when the behavior is
  reverted. A red test beats a comment a future session will read past.
- **Decisions reached in conversation go to persistent memory** so they survive the session that
  produced them, rather than relying on cross-session recall. Reserve numbered ADRs for genuine
  architecture forks with live alternatives; implementation-level choices belong inline or in a
  guard test, not in `docs/decisions/`.
