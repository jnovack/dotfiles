---
id: testing-philosophy
scope: global
order: 26
---

## Testing Philosophy

Language-agnostic rules for what makes a test worth writing. Language and
framework mechanics live in the per-language templates.

- Test negative cases with the same rigor as positive cases: for every happy
  path, consider invalid input, missing data, permission denied, timeout,
  partial failure, and resource exhaustion. A function with one positive test
  and no negative tests is undertested regardless of coverage percentage.
- Prefer the smallest test level that can prove correctness. Do not reach for an
  end-to-end test when a unit or integration test would cover the behavior.
- When fixing a bug, add the narrowest regression test that would have failed
  before the fix.
- Every test must be independent — no shared mutable state between tests.
- Mock external I/O (network, database, filesystem) at the boundary, not deep
  inside implementation code.
- Do not write brittle tests that depend on timing guesses, arbitrary sleeps,
  pixel layout, incidental text formatting, or internal implementation details
  unless the requirement explicitly depends on them.
- If no test is added, explain why the change is low risk or already covered by
  existing tests.
