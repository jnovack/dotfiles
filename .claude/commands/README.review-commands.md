# Review Skill System

A set of three Claude Code slash commands for structured code and test review. The review commands produce a dense,
actionable report with severity-scored findings; the fix command closes findings one at a time, each validated against
build, vet, lint, and tests before it is accepted.

## Why this exists

Code review feedback without a forcing function never lands. Findings stall in a document, fixes get applied
inconsistently, and the report drifts out of sync with the actual code. This system ties review output to a structured
fix workflow: every finding has an ID, every fix has a verify gate, and the report shrinks only when a change has
passed that gate.

## Lifecycle

```text
source code → /review or /review-tests → REVIEW.md → /review-fix → clean tree
```

| Stage | Meaning |
| --- | --- |
| REVIEW.md | Open findings; shrinks as fixes are accepted |
| Finding ID | Unique identifier scoped per file and issue class |
| Verify gate | Build + vet + lint (new issues only) + tests — must all pass before a finding is accepted |
| Removed | Finding deleted from REVIEW.md; fix is in the tree, uncommitted |

## File layout

```text
~/.claude/commands/          <- these skill files (global, works in any repo)
  review.md
  review-tests.md
  review-fix.md

<repo>/
  .local/
    REVIEW.md                <- findings from /review
    REVIEW.TESTS.md          <- findings from /review-tests
    .gitignore               <- auto-created; excludes .local/ from commits
```

## Finding IDs

```text
#<MODULE>-<TYPE>-<N>
```

- **MODULE** — 2–4 char uppercase abbreviation of the filename or module (e.g., `AUTH`, `DB`, `API`, `UI`)
- **TYPE** — 2–4 char uppercase abbreviation of the issue class (e.g., `NULL`, `INJ`, `RACE`, `LEAK`, `SEC`)
- **N** — 1-based integer scoped per file, resetting per module/type combination

Examples: `#AUTH-NULL-1`, `#DB-INJ-1`, `#API-VAL-2`

For test reviews, MODULE reflects the test suite (`INT`, `UNIT`, `E2E`) and TYPE reflects the test failure mode
(`MSG`, `TAUTO`, `GAP`, `MOCK`).

## Severity levels

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Exploitable vulnerability, data loss risk, or crash in normal usage |
| 🟠 High | Likely bug or significant security weakness; fix before shipping |
| 🟡 Medium | Inconsistency or practice violation that will cause problems at scale |
| 🔵 Low | Minor refinement; fix when you're already touching the file |

For test reviews:

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Test actively masks an exploitable bug or data-loss scenario already in production |
| 🟠 High | Test passes when the feature it covers is broken (false confidence) |
| 🟡 Medium | Missing coverage for a significant branch, or assertion tests implementation detail instead of requirement |
| 🔵 Low | Minor message inaccuracy or dead infrastructure |

## Commands

### `/review`

Reviews the entire repository and writes `.local/REVIEW.md`. Reads every source file before writing — no partial results.

Scope:

- **Bugs** — logic errors, off-by-one, null dereferences, incorrect error handling, race conditions, resource leaks
- **Security** — injection risks, insecure defaults, hardcoded secrets, improper input validation, exposed sensitive data
- **Inconsistencies** — deviations from conventions already established in this codebase
- **Best-practice violations** — only issues rooted in well-established patterns for the language and framework in use

```text
/review
→ Reads every source file
→ Writes .local/REVIEW.md with Finding Index + per-file sections
→ Next: /review-fix to apply fixes
```

REVIEW.md structure:

```text
# Code Review

## Summary              <- 3–5 sentence executive summary
## Finding Index        <- master table: ID, severity, file, title
## Findings by File     <- per-file blocks ordered by highest severity
## Severity Reference
## Quick Wins           <- 3–5 highest-leverage changes across the repo
```

### `/review-tests`

Reviews all test files and writes `REVIEW.TESTS.md` at the project root.

Scope:

- **Mirror tests** — assertions that pass regardless of whether the feature works (tautological, testing internal state)
- **Mislabeled tests** — test name describes one path, setup exercises a different path
- **Missing business constraints** — error recovery, auth branches, input combinations not covered
- **Happy path bias** — tests that only verify no crash, without asserting correct outcome
- **Fragile mocking** — mocks that both provide and assert the same value
- **Dead test infrastructure** — fixtures, helpers, or mock types defined but never referenced

```text
/review-tests
→ Reads every test file and corresponding production code
→ Writes REVIEW.TESTS.md with Finding Index + per-file sections
→ Next: /review-fix to apply fixes (reads from .local/REVIEW.md;
         review-fix does not currently target REVIEW.TESTS.md)
```

### `/review-fix [filter]`

Fixes findings from `.local/REVIEW.md` one at a time in severity order (Critical → High → Medium → Low). Each finding
must pass the full verify gate before it is accepted and removed from the report.

**Filters:**

| Invocation | Targets |
| --- | --- |
| `/review-fix` | every open finding |
| `/review-fix high` | all High findings |
| `/review-fix medium and low` | all Medium + Low findings |
| `/review-fix #AUTH-NULL-1` | only `#AUTH-NULL-1` |
| `/review-fix all except #VAL-LOGIC-1` | everything except `#VAL-LOGIC-1` |

**Per-finding procedure:**

1. Load the finding from REVIEW.md
2. Re-validate against current source (finding may already be fixed; line numbers may have drifted)
3. Check impact radius via `code-review-graph` tools before touching anything
4. Apply the smallest correct edit
5. Add or update a test that fails on pre-fix behavior and passes after
6. Sync documentation (GoDoc, README, ADRs, OpenAPI spec, env examples)
7. Run the verify gate — all must pass or the command hard-stops:
   - `go build ./...`
   - `go vet ./...`
   - `golangci-lint run --new-from-rev=$(git merge-base HEAD main)` (new issues only)
   - `make test`
8. Remove the finding from REVIEW.md and the Finding Index table

**Fix-accuracy tier rule** — when the report's proposed fix is wrong:

| Severity | Behavior |
| --- | --- |
| Low | Auto-correct: apply the smallest correct fix, note the deviation in the final report |
| Medium / High / Critical | Stop and ask: explain what is wrong, propose a corrected solution, apply nothing until accepted |

**Hard stops** — the command stops immediately (does not revert, leaves the tree dirty) on:

- Any verify gate failure
- Impact radius too large to cover safely in this pass
- Medium+ fix accuracy rejection (pending operator decision)

```text
/review-fix critical
→ Processes all Critical findings in severity order
→ For each: validates, applies fix, runs tests, removes from REVIEW.md
→ Stops at first gate failure or oversized blast radius
→ Final report: fixed / auto-corrected / skipped / stopped-at / remaining
→ Working tree is dirty and uncommitted — review diffs before committing
```

## Typical session

```text
/review                       <- generate REVIEW.md
/review-fix critical high     <- fix the high-priority items first
                              <- review the diffs, commit when satisfied
/review-fix medium low        <- address the remaining items
                              <- review the diffs, commit when satisfied
/review-tests                  <- generate REVIEW.TESTS.md separately
```

## Notes

- Neither `/review` nor `/review-tests` modifies source files — they only produce report files.
- `/review-fix` never branches, stages, or commits. The working tree is always left dirty for operator review.
- If REVIEW.md is missing or the filter matches zero findings, `/review-fix` reports that and stops without changing anything.
- The verify gate uses `--new-from-rev` lint to measure only what the fix introduced — a pre-existing lint baseline
  cannot mask a new warning or falsely block a finding.
