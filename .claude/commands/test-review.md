Review all test files in the repository and produce a file named REVIEW.TESTS.md at the root of the project.

## Scope

Analyze all test files (`*_test.go`, `test/`, `spec/`, etc.) for:

- **Mirror tests** — tests that pass only because they mimic the current implementation rather than validating the intended requirement. Includes tautological assertions (`A == A`), assertions on internal state instead of user-visible behavior, and tests that would still pass if the feature they claim to cover were deleted.
- **Mislabeled tests** — tests whose name describes one code path but whose setup actually exercises a different path. Flag the discrepancy and identify which path is actually reached.
- **Missing business constraints** — compare test logic against the code under test. Identify scenarios the code handles (or mishandles) that no test exercises. Prioritize: error recovery paths, security-relevant branches (auth bypass, input sanitization, credential handling), and any branch reachable only through a specific combination of inputs.
- **Happy path bias** — tests that only verify the system does not crash, without asserting the correct outcome (status code, response body, header values, side effects on disk/state/metrics).
- **Fragile mocking** — tests that mock internal methods or use transports/fakes that both provide and assert the same value, making the test immune to implementation bugs.
- **Dead test infrastructure** — fixtures, mock endpoints, or helper types defined in the test file but never referenced by any test case.

## Ground Rules

- Prefer the smallest correct change. Do not rewrite what works.
- Preserve existing structure, naming, and patterns unless they are the direct cause of a defect.
- Do not perform unrelated refactors, formatting passes, style normalization, or file moves.
- Any suggested new behavior must be backward-compatible and default-off (feature flag, opt-in config, etc.).
- Do not disagree for novelty's sake. Every finding must cite a specific, demonstrable problem.
- If a file has no meaningful issues, omit it from the report entirely.

## REVIEW.TESTS.md Format

Produce REVIEW.TESTS.md with the following structure:

---

# Test Review

> Generated: <date>
> Reviewer: Claude Code
> Scope: <list of test files reviewed>

## Summary

A 3–5 sentence executive summary of the overall test quality, dominant issue patterns, and highest-priority concerns.

---

## Finding Index

A master table of all findings, emitted before the per-file sections:

| ID | Severity | File | Title |
| --- | --- | --- | --- |
| #INT-MSG-1 | 🟠 High | `test/proxy_integration_test.go` | Inverted assertion message on no-store file check |
| #UNIT-TAUTO-1 | 🟡 Medium | `internal/foo/foo_test.go` | Asserts mocked value equals mocked value |

---

## Findings by File

Repeat the following block for each file that has findings, ordered by the highest severity issue present in that file (High first):

### `path/to/file_test.go`

#### 🟠 High — #INT-MSG-1 — <short title>

**Line(s):** 42

**Issue:** Precise description of what is wrong and why it produces a false-passing or false-failing test.

**Fix:**

```language
// exact replacement code here
```

**Rationale:** One sentence naming the testing principle this violates (e.g., "Failure messages must describe the invariant being enforced, not its negation.").

---

## Severity Reference

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Test actively masks an exploitable bug or data-loss scenario already present in production code |
| 🟠 High | Test provides false confidence: it passes when the feature it covers is broken |
| 🟡 Medium | Missing coverage for a significant branch, or assertion tests implementation detail instead of requirement |
| 🔵 Low | Minor message inaccuracy or dead infrastructure; fix when touching the file |

---

## Quick Wins

A bulleted list of the 3–5 highest-leverage changes — things that add the most coverage or remove the most false confidence for the least effort.

---

*End of REVIEW.TESTS.md*

---

## Additional Instructions

- Read every test file before writing REVIEW.TESTS.md. Do not emit partial results.
- For each finding, read the corresponding production code to confirm the behavior the test should be asserting actually exists and is reachable by the test's setup.
- Line numbers must be exact. Verify them against the actual file content before writing.
- Code blocks in Fix sections must be complete, runnable replacements — not pseudocode.
- If a suggested fix requires changes in more than one location, list all locations.
- Do not add encouraging commentary, filler phrases, or meta-notes inside REVIEW.TESTS.md. Keep it dense and actionable.
- Each finding must include a unique identifier using the format `#<MODULE>-<TYPE>-<N>`:
  - **MODULE**: 2–5 char uppercase abbreviation of the test file or test suite (e.g., INT, UNIT, E2E, SOCKS, CACHE)
  - **TYPE**: 2–5 char uppercase abbreviation of the issue class (e.g., MSG, PATH, MISS, TAUTO, GAP, SEC, MOCK)
  - **N**: 1-based integer scoped per file, resetting for each new file
  - Format heading as: `#### 🟠 High — #INT-MSG-1 — <short title>`
- Populate the Finding Index table at the top of REVIEW.TESTS.md with every finding ID before writing per-file sections.
- When identifying missing tests (`GAP` findings), verify the production code path exists and is reachable before flagging it as missing. Do not flag coverage gaps for code that does not exist.
- Distinguish between "not tested at all" (a gap) and "tested incorrectly" (a mirror test or wrong assertion). Use the correct TYPE abbreviation for each.
