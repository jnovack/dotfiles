Review test files and produce `.local/REVIEW.TESTS.md`.

If a path argument is provided (e.g. `/review-tests test/` or `/review-tests src/`), scope discovery to that path. For languages where test files live beside source files (e.g. Go `*_test.go`), also scan the corresponding source files in that path. Otherwise review the full repository.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist, create it with:

```text
*
!.gitignore
```

---

## Scope

Read every test file in scope and its corresponding production code. Analyze for:

- **Absent test coverage** — exported or public functions, methods, behaviors, or integration paths that have no test at all. Distinguish "not tested" (a gap) from "tested incorrectly" (mirror test or wrong assertion). Verify the production code path exists and is reachable before flagging a gap; do not flag coverage gaps for code that does not exist.

- **Layer coverage gaps** — if the codebase has test layers (unit, integration, functional, smoke, e2e), are critical paths covered at the appropriate layer? Flag a unit-only path that crosses a component boundary, or a missing smoke test for a user-visible critical path.

- **Mirror tests** — tests that pass only because they mimic the current implementation rather than validating the intended requirement. Includes tautological assertions (`A == A`), assertions on internal state instead of user-visible behavior, and tests that would still pass if the feature they claim to cover were deleted.

- **Mislabeled tests** — tests whose name describes one code path but whose setup exercises a different path. Flag the discrepancy and identify which path is actually reached.

- **Missing business constraints** — compare test logic against the production code. Identify scenarios the code handles (or mishandles) that no test exercises. Prioritize: error recovery paths, security-relevant branches (auth bypass, input sanitization, credential handling), and branches reachable only through a specific combination of inputs.

- **Happy path bias** — tests that only verify the system does not crash, without asserting the correct outcome (status code, response body, header values, side effects on state, disk, or metrics).

- **Fragile mocking** — tests that mock internal methods or use fakes that both provide and assert the same value, making the test immune to implementation bugs.

- **Dead test infrastructure** — fixtures, mock endpoints, or helper types defined in a test file but never referenced by any test case.

- **Test reliability** — tests that depend on timing, network access, local machine state, global state mutation, execution ordering, or implementation details that will cause flakiness or false failures in CI.

---

## Ground Rules

- Prefer the smallest correct change. Do not rewrite what works.
- A minimal test fix that contradicts a governing ADR or documented testing
  strategy is not minimal — it is wrong. If the smallest patch conflicts with
  either, report the correct fix instead and say why.
- Preserve existing structure, naming, and patterns unless they are the direct cause of a defect.
- Do not perform unrelated refactors, formatting passes, or file moves.
- Every finding must cite a specific, demonstrable problem.
- If a file has no meaningful issues, omit it from the report.

---

## Additional Instructions

- Read every test file before writing REVIEW.TESTS.md. Do not emit partial results.
- For each finding, read the corresponding production code to confirm the behavior the test should be asserting actually exists and is reachable by the test's setup.
- Line numbers must be exact. Verify them against the actual file content before writing.
- Fix code blocks must be complete, runnable replacements — not pseudocode.
- If a fix requires changes in more than one location, list all locations.
- No encouraging commentary or meta-notes. Keep findings dense and actionable.
- Each finding ID format: `#MODULE-TYPE-NN`
  - MODULE: 2–5 char uppercase abbreviation of the test file or suite (e.g. `INT`, `UNIT`, `E2E`, `AUTH`, `CACHE`)
  - TYPE: 2–5 char uppercase abbreviation of the issue class (e.g. `GAP`, `MISS`, `TAUTO`, `MSG`, `MOCK`, `FRAG`, `DEAD`, `RELY`, `LAYER`)
  - NN: 2-digit 1-based integer, reset per module-type pair
- Distinguish "not tested at all" (`GAP`) from "tested incorrectly" (`TAUTO`, `MOCK`, etc.).

---

## REVIEW.TESTS.md Format

Produce REVIEW.TESTS.md with the following structure:

### Header

```markdown
# Test Review

> Generated: [datetime in localtime]
> Reviewer: Claude Code
> Scope: [list of test files reviewed]
```

### Summary

3–5 sentence executive summary of overall test quality, dominant issue patterns, and highest-priority concerns.

### Finding Index

| ID | Severity | File | Title |
| --- | --- | --- | --- |
| #INT-GAP-01 | 🟠 High | `test/proxy_integration_test.go` | Exported handler has no test |
| #UNIT-TAUTO-01 | 🟡 Medium | `internal/foo/foo_test.go` | Asserts mocked value equals mocked value |

### Findings by File

One block per file that has findings, ordered by highest severity in that file.

#### 🟠 High — #INT-GAP-01 — [short title]

**Line(s):** 42

**Issue:** Precise description of what is wrong and why it produces false confidence or missing coverage.

**Fix:**

```language
// exact replacement or new test code here
```

**Rationale:** One sentence naming the testing principle this violates.

---

### Severity Reference

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Test actively masks an exploitable bug or data-loss scenario in production |
| 🟠 High | Test passes when the feature it covers is broken (false confidence) |
| 🟡 Medium | Significant coverage gap, or assertion tests implementation detail instead of requirement |
| 🔵 Low | Minor message inaccuracy, dead infrastructure, or reliability smell |

### Quick Wins

A bulleted list of the 3–5 highest-leverage changes — things that add the most coverage or remove the most false confidence for the least effort.
