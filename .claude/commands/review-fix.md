# /review-fix

Fix findings recorded in `.local/REVIEW.md` — one finding at a time, each fully
validated, regression-guarded, tested, and documented before it is accepted and
removed from the report.

Arguments: `$ARGUMENTS` (a filter selecting which findings to fix; see **Target
selection**). When empty, every open finding is targeted.

---

## Operating rules (non-negotiable)

- **Source of truth.** `.local/REVIEW.md` lists the open findings. `AGENTS.md`
  governs validation, Definition of Done, and documentation sync; obey it.
- **Smallest correct change.** Apply the fix in the finding (or a corrected
  version of it — see step 2), nothing more. No drive-by refactors, no
  formatting passes, no file moves.
- **No git.** Never branch, stage, or commit. Leave the working tree dirty for
  the operator to review and commit. The REVIEW.md diff plus the code diff are
  the audit trail.
- **Stop on first failure.** Process targets in severity order (Critical → High
  → Medium → Low). On any **verify-gate** failure (build, vet, lint, tests) or an
  impact radius too large to cover safely, **stop**: report what failed with
  output, leave all work in place (do not revert), and do not touch the remaining
  findings. Fix-*accuracy* problems follow the **tier rule** (step 2), not this
  hard stop.
- **Fix-accuracy tier rule.** When the report's proposed fix is wrong, unsafe, or
  incomplete: **Low** findings are auto-corrected (apply your own smallest correct
  fix and note the deviation); **Medium / High / Critical** findings stop and ask,
  and an accepted alternative restarts validation from a clean slate. Full
  mechanics in step 2.
- **Graph first.** Use the `code-review-graph` MCP tools (`semantic_search_nodes`,
  `query_graph`, `get_impact_radius`, `get_affected_flows`) before Grep/Read,
  per `CLAUDE.md`.
- **Pre-release repo conventions** (from project memory — apply without asking):
  - Remove things outright; no deprecation aliases, shims, or transition periods.
  - A change to any one `cmd/` binary or shared package must be applied
    uniformly to every sibling that shares the pattern.
  - Update mock/stub types in `_test.go` files in the **same pass** as the
    production type they mirror.
  - Any flag/env change updates `.env.example` **and** `README.md` in the same pass.
  - Inline comments explain **why** (the invariant/root cause). Never write
    step-reference comments like `// Step N.x:` — they are stripped each phase.

---

## Target selection

Parse `$ARGUMENTS` case-insensitively. Ignore filler words (`all`, `and`, `for`,
`the`, commas). Tokens are either **severities** (`critical`, `high`, `medium`,
`low`) or **finding IDs** matching `#[A-Z0-9]+-[A-Z0-9]+-\d+`.

1. **Inclusion set:**
   - No severity/ID tokens, or the word `all` alone → every open finding.
   - One or more severities → all open findings of those severities.
   - One or more IDs → exactly those findings (ignore severity in this case
     unless severities are also present, in which case union them).
2. **Exclusion set:** tokens after `except`, `except for`, or `but not` are
   removed from the inclusion set (IDs or severities).
3. Final targets = inclusion − exclusion, ordered Critical → High → Medium → Low.

Examples:

| Invocation | Targets |
| --- | --- |
| `/review-fix` | every open finding |
| `/review-fix all high` | all High findings |
| `/review-fix medium and low` | all Medium + Low findings |
| `/review-fix #SET-SEC-1` | only `#SET-SEC-1` |
| `/review-fix all except #VAL-LOGIC-1` | everything but `#VAL-LOGIC-1` |
| `/review-fix except for #FS-RACE-1` | everything but `#FS-RACE-1` |

If `.local/REVIEW.md` is missing, or the filter matches zero findings, report
that and stop without changing anything.

---

## Per-finding procedure

Run these steps in order for one finding. Any **STOP** condition ends the whole
command (stop on first failure).

### 1. Load the finding — read it completely before proceeding

**This step must finish before any other tool is called.** Do not open a source
file, run a shell command, or call any graph tool until this step is done.

Read the finding's **entire block** from `.local/REVIEW.md`: ID, severity, file,
`Line(s)`, Issue, Fix, Rationale, Test — **and every line that follows**, including
any Codex Evaluation, Codex Suggested Fix, alternative fix analysis, reviewer
annotations, or other appended content. The finding block ends where the next
finding's `####` heading begins (or at end of file).

Context below the standard fields often contains a preferred or corrected fix that
supersedes the Fix field. Ignoring it is a correctness error. Read everything,
form a complete picture of the recommended approach, then proceed to step 2.

### 2. Re-validate accuracy against current source

REVIEW.md may be stale relative to the working tree. Open the cited file and
confirm the defect still exists. Line numbers drift — locate the real symbol via
`semantic_search_nodes` / `query_graph` rather than trusting the line range.

- If the defect is **already resolved** in the tree → remove the finding from
  REVIEW.md (step 8 cleanup) with a note "already fixed", and continue to the
  next target (this is success, not a failure).
- If the finding's proposed **Fix is wrong, unsafe, or incomplete**, or you cannot
  confidently locate the code, apply the **fix-accuracy tier rule** by severity:
  - **Low → auto-correct.** Derive the smallest correct fix yourself and proceed
    through steps 3–8 with it. Record the deviation in the final report (what the
    report proposed vs. what you applied, and why). The verify gate (step 7) still
    governs — a gate failure on the corrected fix is still a hard STOP.
    **Exception:** if the corrected fix is non-trivial (e.g. a new package, a
    behavioral split across callers, or a change that touches more than ~5 files),
    stop and present the approach before applying — treat it like a Medium finding
    for that step only, then continue autonomously once accepted.
  - **Medium / High / Critical → stop and ask.** **STOP**. Explain precisely what
    is wrong with the proposed fix and propose a corrected solution (concrete code
    or approach). Apply nothing. If the operator accepts the proposal, **restart
    this finding from step 1 on a clean slate** (see below).

**Clean-slate restart.** When an operator accepts a proposed alternative for a
Medium+ finding, treat that proposal as a *new candidate fix to validate*, not as
pre-approved truth. Re-run this finding's procedure from step 1: re-read the
source fresh, re-run the graph impact check, and re-apply every gate. Humans and
agents both err — the restart makes the accepted solution earn the same full
validation as any other, with no reliance on the prior (rejected) analysis.

### 3. Regression guard via the graph

Run `get_impact_radius` on the symbol(s) you will change and `get_affected_flows`
for the touched files. Read the callers/dependents the fix could break. If the
change ripples to sibling call sites or other `cmd/` binaries, you must update
them all in this pass (consistency rule). If the blast radius is larger than the
fix can safely cover here → **STOP** and report.

### 4. Apply the fix

Make the smallest correct edit, matching surrounding style and naming. Add an
inline comment only if the **WHY is genuinely non-obvious** — a hidden
constraint, a subtle invariant, a workaround for a specific bug. Do not comment
what the code does; do not write step-reference or changelog prose. Most fixes
need no comment at all.

### 5. Lock the fix with a test

Add or update a test that **fails on the pre-fix behavior and passes after**.
Prefer table extension in the existing `_test.go` for that package. State in the
test name/comment which finding it locks (e.g. the defect, not the finding ID, so
the test reads naturally). Update any mock/stub types in test files in the same
pass. If a regression test is genuinely infeasible, say so explicitly in the
final report and explain why.

### 6. Sync documentation

- **GoDoc:** update the doc comment of any function/type whose contract or
  behavior changed so it matches reality.
- **External markdown:** update anything that documents the changed behavior —
  `README.md`, `AGENTS.md`, relevant ADRs under `docs/decisions/`, and
  `docs/openapi.yaml` if an API contract changed. Keep markdown lint-clean per
  `CLAUDE.md` (MD022/MD032/MD040/MD060; blank lines around fences/lists/headings).
- **Flags/env:** if a flag or environment variable changed, update
  `.env.example` and `README.md` together.

### 7. Verify gate — ALL must pass

Run each; any failure → **STOP**, report the command and its output, leave work
in place:

1. `go build ./...`
2. `go vet ./...`
3. **Lint (new issues only):**
   `go run github.com/golangci/golangci-lint/cmd/golangci-lint@latest run --new-from-rev=$(git merge-base HEAD main)`
   — flags only lint issues the change introduces relative to the merge-base with
   the default branch. Block on **any** output. Using `--new-from-rev` instead of
   plain `make lint` means a red baseline can neither mask a real new warning nor
   falsely block the finding; the gate measures exactly what this change added.
   (If `main` is unavailable, substitute the actual default branch ref.)
4. `make test` (full unit/mock suite) — block on any failure.
5. The new/updated test from step 5 is included in `make test` and passes.
6. Touched `.md` files are lint-clean (rely on IDE diagnostics; `markdownlint`
   is not installed here).

### 8. Accept and remove from the report

Only after every gate passes:

- Delete the finding's entire per-file section from `.local/REVIEW.md`.
- Delete its row from the **Finding Index** table.
- If that was the last finding under a `### path/to/file` heading, remove the now-empty heading block.
- Keep `.local/REVIEW.md` lint-clean and internally consistent.

Do **not** commit. Move to the next target.

---

## Final report

After the run (whether it completed or stopped early), print a concise summary:

- **Fixed:** for each accepted finding — ID, files touched, test added, docs updated.
- **Auto-corrected (Low):** any Low finding where you applied a fix that differed
  from the report — note the report's proposal vs. what you applied and why.
- **Skipped (already fixed):** any findings step 2 found already resolved.
- **Stopped at:** if halted — the finding ID, the gate/step that failed (verify
  gate, oversized impact, or a Medium+ proposed-fix rejection), the failing output
  or your corrected proposal, and the recommended next action.
- **Remaining:** open findings still in `.local/REVIEW.md`.
- Remind the operator: the working tree is **dirty and uncommitted** — review the
  `.local/REVIEW.md` diff and the code diff, then commit when satisfied.
