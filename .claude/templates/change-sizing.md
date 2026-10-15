---
id: change-sizing
scope: global
order: 20
---

## Change Sizing: Correct, Not Just Small

"Smallest correct change" sizes the *diff*, not the *decision*. Before sizing a
fix, read the doc comment, the nearest ADR, and the purpose of the flow it sits
in; the fix must fit that intent, not just compile and pass tests.

- A patch that contradicts an ADR, duplicates logic an ADR centralized, or
  reaches around a deliberate interface boundary is wrong however small: fix
  the cause, or propose an ADR change.
- Prefer extending an existing abstraction over adding a parallel special case.
- When correctness and size conflict, make the larger change and say why the
  smaller one would have been wrong.
- This binds review/fix agents too: a finding's `Fix` is a proposal to check
  against intent, not a mandate because it is small and already written.
