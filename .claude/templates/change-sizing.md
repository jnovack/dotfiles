---
id: change-sizing
scope: global
order: 20
---

## Change Sizing: Correct, Not Just Small

"Smallest correct change" describes the *diff*, not the *decision*. A
one-line patch that contradicts an ADR, bypasses a documented invariant, or
papers over a structural problem in the surrounding flow is not a smallest
correct change — it is a workaround wearing a small diff.

### Check intent before sizing

Read the function/type's doc comment, the nearest ADR (see the Architecture
Decision Records rules, if this project keeps them), and the
purpose of the flow the change sits in. A fix must fit that intent, not just
compile and pass tests.

### A minimal fix that violates documented intent is not minimal — it is wrong

If the smallest patch that makes symptoms go away requires contradicting an
ADR, duplicating logic an ADR already centralized, or reaching around an
interface boundary that exists on purpose, the *real* smallest correct change
is larger: fix the actual cause, or explicitly propose an ADR change. Do not
silently pick the smaller, wrong option.

### Prefer extending an existing shape over adding a parallel one

If a fix needs a new special case, ask whether it belongs inside an existing
abstraction (which may mean a slightly larger diff to that abstraction)
rather than beside it as a standalone conditional. Two near-identical code
paths cost more long-term than one larger diff today.

### When correctness and size conflict, size loses — but say so

Make the larger, correct change, and state plainly why the smaller version
would have been wrong. Silence here is how duct tape accumulates.

### This applies to review/fix agents too

Any command or subagent that proposes or applies a fix — human-facing or
automated — is bound by this. A generated finding's `Fix` is a proposal to
check against intent before it is written down or applied, not a mandate to
follow because it is small and already on the page.
