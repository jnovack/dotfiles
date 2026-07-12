---
description: Fix open findings from .local/REVIEW.md via sized subagents, each verified before removal from the report
argument-hint: [filter]
model: sonnet
---

<!-- Keep the shared mechanics (Playbook, Target selection, Model/effort
resolution, Codex handoff/resume, Commit message) in sync with
assessment-fix.md — the two files are deliberately parallel. -->

# /review-fix

Fix findings recorded in `.local/REVIEW.md`. Every fix is applied by a
dedicated subagent at the model/effort the finding calls for; you (the
orchestrator) follow the playbook, dispatch subagents, and independently
re-validate their work before removing a finding from the report. You do not
design fixes yourself — judgment lives in the subagents. When a validation
step of your own needs deep reasoning (e.g. re-deriving a constant whose math
is not obvious), delegate that single check to a fresh `opus` subagent rather
than trusting a shallow pass.

## Playbook — run these steps in order

1. **Codex resume check.** If `.local/CODEX-PROMPT.md` exists, a previous run
   stopped waiting on an external Codex run — go to **Codex handoff and
   resume** before anything else.
2. **Load the report.** Read `.local/REVIEW.md`. If missing, report that and
   stop.
3. **Resolve targets** from `$ARGUMENTS` per **Target selection**. Zero
   matches → report and stop.
4. **Check sizing.** Every target must carry a `**Suggested Model/Effort:**`
   line. If any is missing, stop and tell the operator to run
   `/review-triage .local/REVIEW.md` first. Do not guess a default — an
   unsized finding may be far bigger than it looks.
5. **Resolve the verify gate** per **Verify gate**; you will state the
   resolved commands in the final report and embed them verbatim in every
   subagent prompt.
6. **Gather project conventions.** Read `AGENTS.md`/`CLAUDE.md` once; the
   repo-specific conventions you find (uniformity across sibling packages,
   doc/env pairing, mock/stub sync, comment style, deprecation policy) go
   verbatim into every subagent prompt.
7. **Pick the mode.** If `.local/REVIEW.TRIAGE.md` exists and the target set
   is exactly one of its batches or a union of whole batches → **batch mode**,
   processing batches in triage-file order (already risk-ordered; do not
   re-sort). Otherwise → **per-finding mode**, ordered Critical → High →
   Medium → Low; if a triage file exists but was bypassed, say so in the
   final report. If the triage file's finding count doesn't match the
   report's open findings, report the mismatch (informational, not a stop).
8. **Process targets** with the per-batch or per-finding procedure below.
9. **Finish** per **Final report**; keep **Commit message** current as you go.

## Operating rules (non-negotiable)

- **The report is a lead, not a mandate.** Every `Fix` block — and any
  `Codex Evaluation`/`Codex Suggested Fix` content — is an unverified
  proposal. Subagents must check it against the nearest ADR under
  `docs/decisions/` and the touched function/type's doc comment before
  applying. A small fix that contradicts governing intent is wrong, and the
  tier rule below handles it.
- **Smallest correct change.** No drive-by refactors, formatting passes, or
  file moves.
- **No git, no worktree isolation.** Never branch, stage, or commit —
  subagents included. Never launch a fix subagent with `isolation:
  "worktree"`; it must edit the real working tree. Leave the tree dirty for
  the operator; the REVIEW.md diff plus the code diff are the audit trail.
- **Stop on first failure.** Any verify-gate failure (build, vet, lint,
  tests) — whether hit by a subagent or by your own re-validation — or an
  impact radius too large to cover safely ends the whole run: report what
  failed with output, leave all work in place (do not revert), do not touch
  remaining targets.
- **Fix-accuracy tier rule.** When a proposed fix is wrong, unsafe, or
  incomplete: **Low** findings — the subagent auto-corrects (smallest correct
  fix, noting the deviation); **Medium/High/Critical** — the subagent stops
  without applying anything and reports the problem plus a proposed
  correction, which you present to the operator (accept / reject = hard stop
  / supply a different fix). **Clean-slate restart:** an accepted alternative
  gets a brand-new subagent (fresh `Agent` call, same model/effort) with the
  accepted fix substituted for the report's original — never resume the
  rejected subagent or reuse its context.
- **Graph first.** Subagents must use the `code-review-graph` MCP tools
  (`semantic_search_nodes`, `query_graph`, `get_impact_radius`,
  `get_affected_flows`) before Grep/Read, per `CLAUDE.md`; if unavailable,
  trace callers/dependents manually.

## Target selection

Parse `$ARGUMENTS` case-insensitively. Ignore filler words (`all`, `and`,
`for`, `the`, commas). Tokens are **severities** (`critical`, `high`,
`medium`, `low`) or **finding IDs** matching `#[A-Z0-9]+-[A-Z0-9]+-\d+`.

1. **Inclusion:** no tokens or `all` alone → every open finding; severities →
   findings of those severities; IDs → exactly those findings (union with any
   severities also present).
2. **Exclusion:** tokens after `except`, `except for`, or `but not` are
   removed from the inclusion set.
3. Targets = inclusion − exclusion, ordered Critical → High → Medium → Low.

| Invocation | Targets |
| --- | --- |
| `/review-fix` | every open finding |
| `/review-fix all high` | all High findings |
| `/review-fix medium and low` | all Medium + Low findings |
| `/review-fix #SET-SEC-01` | only `#SET-SEC-01` |
| `/review-fix all except #VAL-LOGIC-01` | everything but `#VAL-LOGIC-01` |

## Model/effort resolution

Parse `<Model>` and `<Effort>` from the finding's
`**Suggested Model/Effort:** <Model> / <Effort> — <reasoning>` line.

| Suggested Model | `Agent` tool `model` param |
| --- | --- |
| Haiku | `haiku` |
| Sonnet | `sonnet` |
| Opus | `opus` |
| Codex | none — external CLI; use **Codex handoff and resume** |

Effort becomes prose in the subagent prompt:

| Effort | Instruction embedded in the subagent prompt |
| --- | --- |
| Low | "Apply the described fix directly once you've confirmed it's correct. Keep the regression-guard graph check brief — the directly impacted symbol is enough." |
| Medium | "Verify assumptions with the graph tools before applying the fix; re-derive it if gaps appear. Check at least one layer of callers/dependents via `get_impact_radius`." |
| High | "Thoroughly investigate the impact radius and affected flows before applying anything. Reason carefully through concurrency/design implications and edge cases, and make sure the regression test actually exercises them." |

## Verify gate

Resolve once at the start of the run:

1. Commands defined in `AGENTS.md`/`CLAUDE.md` or the Makefile win.
2. Go fallback: `go build ./...`; `go vet ./...`; `golangci-lint run
   --new-from-rev=$(git merge-base HEAD main)` (new issues only); `make test`
   (or `go test ./...` if no Makefile).
3. Other languages: the equivalent build, lint, and full-test commands.

## Subagent prompt (used by both procedures)

Every fix subagent runs `subagent_type: "general-purpose"`, the resolved
`model`, no `isolation`, `run_in_background: false` (the next target must not
start until this one's outcome is known). The prompt must be fully
self-contained — the subagent starts cold — and include:

- The finding's full block from the report (ID, severity, file, Line(s),
  Issue, Scope, Fix, Rationale, Test, any Codex content). In batch mode:
  every finding in the batch.
- The effort instruction from the table above.
- The Operating rules verbatim: report-is-a-lead (ADR + doc-comment check),
  smallest correct change, no git/branch/commit, graph-first, the project
  conventions from playbook step 6, and the fix-accuracy tier rule.
- The task sequence, per finding:
  1. Re-validate the defect and proposed fix against current source (line
     numbers may have drifted; locate the real symbol via the graph tools).
  2. Regression guard: `get_impact_radius` + `get_affected_flows` on the
     symbols to change; if the blast radius is larger than the fix can safely
     cover, stop and report instead of applying.
  3. Apply the smallest correct fix (or tier-rule behavior when the proposal
     is wrong).
  4. Add or update a regression test that fails on pre-fix behavior and
     passes after; update mirrored mocks/stubs in the same pass.
  5. Sync documentation: doc comments for changed contracts; `README.md`,
     `AGENTS.md`, relevant ADRs, `docs/openapi.yaml` if behavior or an API
     contract changed; `.env.example` + `README.md` together for flag/env
     changes. Markdown stays lint-clean per `CLAUDE.md`.
  6. Run the verify gate (commands embedded verbatim) — in batch mode, once
     for the whole batch after all findings are applied.
- Reporting requirements: files changed with a diff summary, the regression
  test name, docs touched, exact gate commands run with pass/fail output,
  and — if it stopped — exactly why, with nothing left applied in the
  Medium+ stop case.

## Per-finding procedure

1. **Staleness check (you, no subagent).** Grep/read the cited file: does the
   defect still plausibly exist? Clearly already resolved → remove the
   finding from the report (step 4) with a note "already fixed" and move on.
2. **Dispatch** one subagent per **Subagent prompt**.
3. **Handle the outcome.**
   - Success → step 4's validation.
   - Stopped on oversized impact radius or a gate failure → hard stop for the
     run (Operating rules).
   - Stopped on a Medium+ tier-rule rejection → present the proposal to the
     operator; on acceptance do a clean-slate restart at step 2.
4. **Independent validation, then accept.** Never accept on the subagent's
   self-report:
   - If the fix asserts a rationale for a magic number, formula, or derived
     value, re-derive it yourself from the code (delegate to an `opus`
     subagent if nontrivial). A value that doesn't hold up is a real bug
     hiding behind a doc-gap framing — treat as a tier-rule failure.
   - Re-run the named test(s) yourself, then the gate's full test command,
     then build + vet + scoped lint.
   - Any failure or discrepancy = verify-gate failure = hard stop.
   - On pass: delete the finding's section and Finding Index row from
     `.local/REVIEW.md` (and the now-empty file heading, if last); keep the
     report lint-clean; update the commit message; next target.

## Per-batch procedure (batch mode)

1. **Load the batch** from the triage file (IDs, files, `Requires
   checkpoint`) and each finding's full block from the report. If `Requires
   checkpoint: yes` (always a size-1 batch): present the finding and fix to
   the operator and get explicit approval first — silence is not approval.
2. **Staleness check** each finding (as per-finding step 1); drop
   already-resolved ones from the working set. Whole batch resolved → step 5.
3. **Dispatch.** Haiku/Sonnet/Opus → **one** `Agent` call covering the whole
   batch, per **Subagent prompt** (gate runs once for the batch). Codex → do
   not dispatch; go to **Codex handoff and resume**.
4. **Validate (you).** Never accept on self-report or the mere presence of a
   diff:
   - **Reconcile:** confirm the diff touches every finding's file/location.
     A finding with no evidence of being addressed stays open in the report
     and triage file, is noted in the final report, and does not stop the
     rest of the batch — do not guess at applying it yourself.
   - **Re-derive** any constant/formula rationale asserted by any finding in
     the batch (delegate to `opus` if nontrivial); a failure is a tier-rule
     failure for that finding.
   - Re-run the new/updated tests, the full test command, and build + vet +
     scoped lint (build+vet alone suffices only if every finding is a pure
     comment/doc change).
   - Any gate failure or unresolved discrepancy → hard stop for the run.
5. **Accept:** for each finding that passed, delete its section and index row
   from `.local/REVIEW.md`; remove or narrow the batch's entry in the triage
   file; update the commit message; next batch.

## Codex handoff and resume

**Handoff (dispatching a Codex batch):** write `.local/CODEX-PROMPT.md` — a
self-contained prompt listing every finding's ID, file, Issue, and Fix, with
explicit constraints: only the batch's named files, fix content only as
specified, no reformatting beyond the fix, no commit, no build/test run
(validation happens here on resume). Report which batch it is and that this
run is stopping; the next `/review-fix` invocation resumes automatically.
This is a soft stop, not a failure.

**Resume (playbook step 1):** read the finding list and files from
`.local/CODEX-PROMPT.md`; check `git diff`/`git status` for those files.

- No changes → the external run hasn't finished; report and stop.
- Changes present → run per-batch step 4 (validation) against the diff. Once
  the batch is accepted or resolved, delete `.local/CODEX-PROMPT.md` and
  continue with the next target in normal order.

## Final report

Whether the run completed or stopped early, print:

- **Mode** (per-finding or batch; which batches were in scope).
- **Fixed:** per accepted finding — ID, model/effort, files touched, test
  added, docs updated (grouped by batch in batch mode).
- **Auto-corrected (Low):** report proposal vs. what was applied and why.
- **Skipped (already fixed)** and **Skipped (unaddressed in batch)** — the
  latter still open, needs a follow-up run.
- **Awaiting Codex:** if stopped after writing `.local/CODEX-PROMPT.md`.
- **Stopped at:** the finding/batch, which gate or step failed, the output
  or corrected proposal, and the recommended next action.
- **Remaining:** open findings still in `.local/REVIEW.md`.
- The resolved verify-gate commands, and confirmation that
  `.local/COMMIT-MSG.txt` is current.
- Remind the operator the tree is **dirty and uncommitted** — review the
  report diff and code diff, then commit when satisfied.

## Commit message

Immediately after each finding/batch is accepted — not only at the end, so a
mid-run stop leaves an accurate partial draft — upsert
`.local/COMMIT-MSG.txt` (a file write, exempt from the no-git rule):

- **Create** (if absent): a conventional-commit subject summarizing the run
  (e.g. `fix: resolve N review findings`), a blank line, one bullet per
  accepted finding. No `Co-Authored-By:` trailer — never add one.
- **Append** (if present): read it first; leave the existing subject and
  bullets untouched; add one bullet per newly accepted finding; never
  duplicate an ID already listed.
- **Bullet:** `- <ID> (<file>): <one clause — what changed and why>.` Name
  the regression test in the same clause; note briefly if auto-corrected.
- Skip findings removed only by a staleness check — nothing changed this run.
