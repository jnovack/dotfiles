---
id: intent-capture
scope: global
requires: [change-sizing, documentation-style]
order: 24
---

## Intent Capture

Claude writes the code and its tests, so Claude records the *why* of any
intentional or non-obvious behavior in the same change, unprompted. Change
Sizing can only respect intent that was written down.

- **Inline at the code point.** Comments and docs lead with why, not what: name
  the failure a naive revert or "simplification" would cause. A reason on the
  changed lines survives refactors; one in chat or a distant file does not.
- **Behavior gets a guard test, not prose.** If it is observable at runtime, add
  a named test that states the decision and fails when it is reverted.
- **Decisions reached in conversation go to persistent memory.** Reserve
  numbered ADRs for architecture forks with live alternatives; implementation
  choices go inline or in a guard test.
