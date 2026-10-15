---
id: commitment-durability
scope: global
requires: [intent-capture]
order: 25
---

## Commitment Durability

Chat is not storage: work deferred only in a response is lost when the session ends.

- Before ending a turn, file every deferred item — open decisions, cleanups,
  circle-backs, things noticed but not fixed, anything "for later" — in
  `.local/TODO.md` via the `todo-add` skill. Do it; don't suggest it.
- Cite each deferred item in the summary by its TODO ID. An item without one is lost.
- For an open decision, record the question and the options in the row.
- TodoWrite dies with the session; it never replaces a TODO row.
- Update memory and tracking files when facts change, not only at wrap-up.
