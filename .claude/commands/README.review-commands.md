# Review Skill System

A set of slash commands for structured code review, comprehensibility
assessment, test review, and dependency review, plus an action-update
executor. Review/assessment commands produce dense, actionable reports with
severity-scored findings. An optional triage pass groups those findings into
batches. The fix commands close findings — one at a time, or batch by batch
— each validated before acceptance.

## Why this exists

Review feedback without a forcing function never lands. Findings stall in a
document, fixes get applied inconsistently, and the report drifts out of
sync with the actual code. This system ties review output to a structured
fix workflow: every finding has an ID and a model/effort assignment, every
fix has a verify gate, and the report shrinks only when a change has passed
that gate. Triage exists because "one finding at a time" is the right
granularity for bug fixes (each needs its own regression test) but wasteful
for a report full of low-ambiguity, same-shape findings — batching those
turns N verification passes into a handful.

## Lifecycle

```text
source code → /review [path]                 → .local/REVIEW.md      ─┐
              /review-comprehensive [path]    → .local/REVIEW.md      ─┤
comprehens.  → /assessment [path]             → .local/ASSESSMENT.md  ─┘
                                                                        │
                                               /review-triage [report] ←┘
                                                        │
                                    .local/REVIEW.TRIAGE.md or
                                    .local/ASSESSMENT.TRIAGE.md
                                                        │
                              /review-fix [filter]  or  /assessment-fix [filter]

test files  → /review-tests [path]           → .local/REVIEW.TESTS.md
dep files   → /review-deps [path]            → .local/REVIEW.DEPS.md
workflows   → /update-actions               → .local/REVIEW.ACTIONS.md + modified files
```

| Stage | Meaning |
| --- | --- |
| REVIEW.md / ASSESSMENT.md | Open findings; shrinks as fixes are accepted |
| Finding ID | Unique identifier scoped per file and issue class |
| Suggested Model/Effort | Per-finding execution sizing; added at generation time or backfilled by `/review-triage` — required before a `-fix` command will process a finding |
| `*.TRIAGE.md` | Optional grouping/ordering index over an open report; planning only, never modifies source or the report itself (besides backfilling the field above) |
| Verify gate | Build + vet + lint (new issues only) + tests — all must pass before a finding is accepted. `/assessment-fix` relaxes this to build+vet for pure comment/doc fixes; a fix that turns out to be a real bug gets the full gate |
| Removed | Finding deleted from its report; fix is in the tree, uncommitted |

## File layout

```text
~/.claude/commands/          <- these skill files (global, works in any repo)
  review.md
  review-comprehensive.md
  assessment.md
  review-triage.md
  review-tests.md
  review-deps.md
  review-fix.md
  assessment-fix.md
  update-actions.md

<repo>/
  .local/
    .gitignore               <- auto-created; excludes .local/ from commits
    REVIEW.md                <- findings from /review or /review-comprehensive
    ASSESSMENT.md             <- findings from /assessment
    REVIEW.TRIAGE.md         <- batch plan for REVIEW.md, from /review-triage
    ASSESSMENT.TRIAGE.md      <- batch plan for ASSESSMENT.md, from /review-triage
    REVIEW.TESTS.md          <- findings from /review-tests
    REVIEW.DEPS.md           <- findings from /review-deps
    REVIEW.ACTIONS.md        <- report from /update-actions
```

## Finding IDs

```text
#<MODULE>-<TYPE>-<NN>
```

- **MODULE** — 2–5 char uppercase abbreviation of the filename or module (e.g. `AUTH`, `DB`, `API`, `MW`)
- **TYPE** — 2–5 char uppercase abbreviation of the issue class (e.g. `NULL`, `INJ`, `RACE`, `LEAK`, `SEC`, `ERR`)
- **NN** — 2-digit 1-based integer, reset per module-type pair

For test reviews, MODULE reflects the test suite (`INT`, `UNIT`, `E2E`) and TYPE reflects the failure mode (`GAP`, `TAUTO`, `MOCK`, `FRAG`, `DEAD`, `RELY`, `LAYER`).

For dependency reviews, MODULE reflects the ecosystem (`GOMOD`, `NPM`, `PY`, `CARGO`) and TYPE reflects the concern (`UNPIN`, `STALE`, `BREAK`, `AUTO`).

For comprehensibility assessments (`/assessment`), MODULE reflects the file/module and TYPE reflects the comprehensibility failure: `DOC` (missing/misleading documentation), `WHY` (missing inline rationale), `GAP` (pattern applied inconsistently), `NAME` (misleading name), `DEAD` (vestigial code), `CNTR` (unstated implicit contract), `STRCT` (structural confusion). `NN` increments globally across the report rather than resetting per module-type pair.

## Severity levels

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Exploitable vulnerability, data loss risk, or crash in normal usage |
| 🟠 High | Likely bug or significant security weakness; fix before shipping |
| 🟡 Medium | Inconsistency or practice violation that will cause problems at scale |
| 🔵 Low | Minor refinement; fix when already touching the file |

For comprehensibility assessments:

| Level | Meaning |
| --- | --- |
| 🔴 Critical | A reader will almost certainly misunderstand this and introduce a defect or wrong assumption during maintenance |
| 🟡 Warning | A reader will need to slow down, cross-reference, or guess; ongoing maintenance risk |
| 🔵 Note | Minor gap; low immediate risk but degrades the codebase over time |

For test reviews:

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Test actively masks an exploitable bug or data-loss scenario in production |
| 🟠 High | Test passes when the feature it covers is broken (false confidence) |
| 🟡 Medium | Significant coverage gap, or assertion tests implementation detail instead of requirement |
| 🔵 Low | Minor message inaccuracy, dead infrastructure, or reliability smell |

For dependency reviews:

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Known CVE in a dependency used in a security-sensitive path |
| 🟠 High | Major version gap with likely breaking changes |
| 🟡 Medium | Moderately stale minor version, missing automation coverage, or floating pin |
| 🔵 Low | Minor version drift on a non-security-sensitive dev dependency |

## Commands

### `/review [path]`

Reviews source files and writes `.local/REVIEW.md`. Scope to a path with `/review src/` or `/review cmd/app1`; omit for the full repository.

Before writing any finding, works through a mandatory 9-item checklist for every file in scope:

1. Absent-value safety (null, nil, typed null, zero-value-invalid)
2. Error/exception propagation (checked, context preserved, not swallowed)
3. Resource lifecycle (handles, connections, goroutines, timers — guaranteed release)
4. Concurrency (synchronized or immutable; async lifetime bounded)
5. Trust boundary validation (user input, env vars, external APIs, HTTP headers)
6. Credential/secret exposure (variables, error messages, logs, traces, metrics)
7. Injection surfaces (queries, shell, templates, paths, regex, archive paths)
8. Test completeness — spot-check only; use `/review-tests` for the full audit
9. Convention consistency with the existing codebase

Only records findings supported by concrete code evidence. Does not flag speculative issues or risks already handled elsewhere.

```text
/review
→ Reads every source file; works through 9-item checklist per file
→ Writes .local/REVIEW.md with Finding Index + per-file sections
→ Next: /review-fix to apply fixes
```

### `/review-comprehensive [path]`

Multi-agent parallel review. Same scope as `/review` but fans out 6 agents simultaneously, each hunting one dimension. Token cost is approximately 5× a standard `/review` run; use when coverage matters more than speed.

```text
/review-comprehensive
→ Discover agent: lists all source files
→ 6 parallel agents: null+errors, resources, concurrency,
  security, test completeness, convention consistency
→ Synthesis agent: deduplicates and writes .local/REVIEW.md
→ Next: /review-fix to apply fixes
```

### `/assessment [path]`

Human-comprehensibility review — not correctness, not performance, not
security. Reads every file in scope and reports where a human engineer would
have to reverse-engineer intent: missing/misleading docs, unstated
rationale, inconsistently-applied patterns, structural confusion, misleading
names, dead code, and implicit contracts. Every finding carries a Suggested
Model/Effort line sized by blast radius and ambiguity — not by severity —
plus a rule to re-derive (not transcribe) any rationale a fix asserts for a
magic number or formula, since that can surface a real bug hiding behind an
"undocumented constant" framing.

```text
/assessment
→ Reads every source file for comprehensibility only (see /review for bugs)
→ Writes .local/ASSESSMENT.md with Finding Index + per-file sections,
  each finding carrying a Suggested Model/Effort line
→ Next: /review-triage .local/ASSESSMENT.md, then /assessment-fix
```

### `/review-triage [report]`

Groups and orders a report's open findings into batches a `-fix` command can
execute efficiently, and writes a companion `*.TRIAGE.md`. Changes no source
code — purely a planning pass. Works on either `.local/REVIEW.md` or
`.local/ASSESSMENT.md` (defaults to whichever exists, preferring REVIEW.md).

Backfills a missing `Suggested Model/Effort` line directly into the source
report for any finding that predates it — a `-fix` command will not process
a finding without one. Groups same-tier, non-dependent findings that touch a
manageable number of files into one batch (never mixing tiers, never
bundling a judgment call — those always get their own batch and a mandatory
checkpoint). Orders batches cheapest/safest first.

```text
/review-triage .local/ASSESSMENT.md
→ Ensures every finding has a Suggested Model/Effort (backfills into
  ASSESSMENT.md if missing)
→ Groups same-tier findings into batches; isolates checkpoint-required
  findings into their own batch each
→ Writes .local/ASSESSMENT.TRIAGE.md, ordered cheapest-first
→ Next: /assessment-fix (processes batches in this order automatically)
```

### `/review-tests [path]`

Comprehensive test audit. Reads every test file and its corresponding production code. Scope to a path with `/review-tests test/`; for languages with co-located test files (e.g. Go), also scans the source in that path.

Scope:

- **Absent test coverage** — exported/public functions, methods, or behaviors with no test at all
- **Layer coverage gaps** — critical paths missing coverage at the appropriate layer (unit/integration/smoke)
- **Mirror tests** — assertions that pass regardless of whether the feature works
- **Mislabeled tests** — test name describes one path, setup exercises another
- **Missing business constraints** — error recovery, auth branches, input combinations not covered
- **Happy path bias** — only verifies no crash, not correct outcome
- **Fragile mocking** — fakes that both provide and assert the same value
- **Dead test infrastructure** — fixtures or helpers defined but never referenced
- **Test reliability** — timing, ordering, global state, or network dependencies

```text
/review-tests
→ Reads every test file and corresponding production code
→ Writes .local/REVIEW.TESTS.md with Finding Index + per-file sections
→ Note: /review-fix does not currently target REVIEW.TESTS.md
```

### `/review-deps [path]`

Dependency hygiene audit. Reads all package manager manifests and lockfiles. Scope to a path with `/review-deps`; omit for the full repository.

Scope:

- **Version pinning** — floating pins (`latest`, `*`, `^`, `~`) that allow silent breaking updates
- **Dependabot / Renovate coverage** — automated update tooling configured per ecosystem
- **Stale major versions** — major version gaps evidenced by the manifest or lockfile
- **Known-vulnerable patterns** — version ranges known to contain CVEs (does not fabricate CVE IDs)

For each High finding, greps the codebase for direct usages and assesses breaking-change risk.

```text
/review-deps
→ Reads all package manifests and lockfiles
→ Writes .local/REVIEW.DEPS.md with Finding Index + per-file sections
→ Note: /review-fix does not target REVIEW.DEPS.md — dependency upgrades require manual validation
```

### `/update-actions`

Upgrades all GitHub Actions `uses:` pins to their latest major release version. Modifies workflow files directly — this is an executor, not a read-only review.

Respects `# wontfix` comments: any `uses:` line annotated with `# wontfix` (case-insensitive) is skipped and noted in the report.

Preserves pin style (replace like for like):

| Current pin style | Updated to |
| --- | --- |
| SHA | SHA of latest release + `# vX.Y.Z` comment |
| `@vX.Y.Z` | `@vX.Y.Z` of latest release |
| `@vX` | `@vX` of latest major |
| Branch (`@main`) | SHA of latest release + `# vX.Y.Z` comment |

For each major-version upgrade, fetches release notes to reconcile interface changes (renamed inputs, removed keys, new required fields) and applies them to the workflow files.

```text
/update-actions
→ Reads all .github/workflows/ files
→ Looks up latest major release for each action via WebFetch/WebSearch
→ Updates uses: pins (preserving pin style; branch pins → SHA)
→ Reconciles interface changes; leaves # TODO comments where manual resolution needed
→ Writes .local/REVIEW.ACTIONS.md with change table per file + wontfix log
→ Working tree is dirty — review diff before committing
```

### `/review-fix [filter]`

Fixes findings from `.local/REVIEW.md`. If `.local/REVIEW.TRIAGE.md` exists
and the resolved filter matches whole batches from it, processes **batch by
batch** — one dispatch and one verify gate per batch — in the triage file's
risk-ordered sequence. Otherwise falls back to one finding at a time in
severity order (Critical → High → Medium → Low). Either way, each finding
must pass the full verify gate before it is accepted and removed from the
report.

A batch assigned the `Codex` model is not run through the `Agent` tool at
all — Codex is a separate vendor's CLI. Instead `/review-fix` writes a
self-contained `.local/CODEX-PROMPT.md` for that batch and stops; the
operator hands it to Codex externally and reports back, and the next
`/review-fix` invocation detects the resulting diff and resumes from
validation automatically.

**Filters:**

| Invocation | Targets |
| --- | --- |
| `/review-fix` | every open finding |
| `/review-fix high` | all High findings |
| `/review-fix medium and low` | all Medium + Low findings |
| `/review-fix #AUTH-NULL-01` | only that finding |
| `/review-fix all except #VAL-LOGIC-01` | everything except that finding |

**Per-finding procedure:**

1. Load the finding from REVIEW.md
2. Re-validate against current source (may already be fixed; line numbers may have drifted)
3. Check impact radius via `code-review-graph` tools before touching anything
4. Apply the smallest correct edit
5. Add or update a test that fails on pre-fix behavior and passes after
6. Sync documentation (docstrings, README, ADRs, OpenAPI spec, env examples)
7. Run the verify gate — all must pass or the command hard-stops:
   - Build (`go build ./...` or equivalent for the project's language)
   - Vet/lint (`go vet ./...`, `golangci-lint run --new-from-rev=$(git merge-base HEAD main)`, or equivalent)
   - Tests (`make test` or equivalent)
8. Remove the finding from REVIEW.md and the Finding Index table

**Fix-accuracy tier rule** — when the report's proposed fix is wrong:

| Severity | Behavior |
| --- | --- |
| Low | Auto-correct: apply the smallest correct fix, note the deviation |
| Medium / High / Critical | Stop and ask: explain what is wrong, propose a corrected solution, apply nothing until accepted |

**Hard stops** — the command stops immediately on:

- Any verify gate failure
- Impact radius too large to cover safely in this pass
- Medium+ fix accuracy rejection pending operator decision

```text
/review-fix critical
→ Processes all Critical findings in severity order
→ For each: re-validates, applies fix, runs verify gate, removes from REVIEW.md
→ Stops at first gate failure or oversized blast radius
→ Working tree is dirty and uncommitted — review diffs before committing
```

### `/assessment-fix [filter]`

Fixes findings from `.local/ASSESSMENT.md`. Same filter syntax and
triage/batch/Codex-handoff mechanics as `/review-fix`, but a lighter verify
gate: build + vet is sufficient for a fix that only touches comments or doc
strings — no test is invented for code that didn't change behavior.

The one non-negotiable step, run independently by the orchestrator even when
a subagent or Codex claims to have done it: before accepting any fix that
explains a magic number, formula, or derived value, re-derive that value
from the code it describes. If it doesn't hold up, the finding just
escalated from a doc gap to a real bug — it gets re-sized, a real code fix,
a regression test, and the full verify gate, same as `/review-fix` would
demand. Findings that require editing a file under `docs/decisions/` (not
just citing one) always require an explicit operator checkpoint, regardless
of what the triage file says.

```text
/assessment-fix warning
→ Processes all Warning findings, batch-by-batch if .local/ASSESSMENT.TRIAGE.md
  matches the filter, else one at a time
→ For each: re-validates, re-derives any asserted constant/formula, applies
  the fix, runs build+vet (or the full gate if it turned out to be a bug)
→ Removes accepted findings from ASSESSMENT.md and ASSESSMENT.TRIAGE.md
→ Working tree is dirty and uncommitted — review diffs before committing
```

## Typical session

```text
/review                        <- generate REVIEW.md (full repo)
/review src/payments           <- generate REVIEW.md (scoped to one package)
/review-fix critical high      <- fix the high-priority items first
                               <- review diffs, commit when satisfied
/review-fix medium low         <- address remaining items
                               <- review diffs, commit when satisfied
/review-tests                  <- comprehensive test audit → REVIEW.TESTS.md
/review-deps                   <- dependency hygiene → REVIEW.DEPS.md
/update-actions                <- upgrade GitHub Actions → REVIEW.ACTIONS.md + modified files
```

When token budget is available:

```text
/review-comprehensive          <- multi-agent parallel review → REVIEW.md
/review-fix                    <- work through all findings
```

Comprehensibility pass, with triage batching for a large report:

```text
/assessment                            <- generate ASSESSMENT.md (full repo)
/review-triage .local/ASSESSMENT.md    <- backfill Model/Effort, group into
                                           batches → ASSESSMENT.TRIAGE.md
/assessment-fix                        <- works through batches cheapest-first;
                                           stops and writes CODEX-PROMPT.md at
                                           any Codex-tier batch
                                       <- hand CODEX-PROMPT.md to Codex, tell
                                           the operator when it's done
/assessment-fix                        <- re-invoke; detects the Codex diff,
                                           validates it, resumes remaining batches
                                       <- review diffs, commit when satisfied
```

## Notes

- `/review`, `/review-comprehensive`, `/assessment`, `/review-triage`,
  `/review-tests`, and `/review-deps` do not modify source files.
  `/review-triage` may modify its source report (backfilling a missing
  `Suggested Model/Effort` line) but never touches code.
- `/update-actions` modifies `.github/workflows/` files directly. The working tree is left dirty for operator review; nothing is staged or committed.
- `/review-fix` and `/assessment-fix` never branch, stage, or commit.
- If the target report is missing or the filter matches zero findings, `/review-fix`/`/assessment-fix` reports that and stops without changing anything.
- A `-fix` command requires every targeted finding to already carry a `Suggested Model/Effort` line; run `/review-triage` first if the report predates that field (older reports, or ones generated before this system existed).
- A batch assigned the `Codex` model always stops the current `-fix` invocation after writing `.local/CODEX-PROMPT.md` — that handoff is inherently a human-in-the-loop step, not something a single command run can complete. The next invocation resumes automatically once it detects the resulting diff.
- The verify gate commands shown are Go examples. For other languages, substitute the equivalent build, lint, and test commands for the project.
- `/review-fix` does not target REVIEW.TESTS.md, REVIEW.DEPS.md, or REVIEW.ACTIONS.md — those reports require manual or purpose-built remediation workflows. `/assessment-fix` targets only ASSESSMENT.md.
