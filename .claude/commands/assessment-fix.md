---
description: Fix comprehensibility findings from .local/ASSESSMENT.md; re-derives asserted constants, lighter gate for doc-only fixes
argument-hint: [filter]
model: sonnet
---

<!-- Keep the shared mechanics (Playbook, Target selection, Model/effort
resolution, Codex handoff/resume, Commit message) in sync with
review-fix.md — the two files are deliberately parallel. -->

# /assessment-fix

Fix findings recorded in `.local/ASSESSMENT.md`. Every fix is applied by a
dedicated subagent at the model/effort the finding calls for; you (the
orchestrator) follow the playbook, dispatch subagents, and independently
re-validate their work before removing a finding from the report. You do not
design fixes yourself — judgment lives in the subagents. When a validation
step of your own needs deep reasoning (above all, re-deriving a constant or
formula whose math is not obvious), delegate that single check to a fresh
`opus` subagent rather than trusting a shallow pass.

**How this differs from `/review-fix`:** review findings are behavior
defects, so every fix gets a regression test; assessment findings are
comprehensibility gaps, and most fixes are pure documentation. So:

- **A fix is a comment until proven otherwise.** Before accepting any fix
  that explains a magic number, formula, derived value, or "why this and not
  that" rationale, re-derive it from the code it describes. Transcribing the
  report's wording is not verification — a real bug once hid behind a
  "document the +6 constant" finding whose constant was simply wrong.
- **If re-derivation fails, the finding just got bigger.** It escalates from
  a doc gap to a real bug: re-size it (at least Sonnet/High), require a code
  fix plus a regression test, run the full gate, and say so explicitly in
  the final report.
- **Everything else gets a lighter gate.** Build + vet is sufficient for a
  fix that only touches comments or doc strings; no test is invented for
  code whose behavior didn't change.

## Playbook — run these steps in order

1. **Codex resume check.** If `.local/CODEX-PROMPT.md` exists, a previous run
   stopped waiting on an external Codex run — go to **Codex handoff and
   resume** before anything else.
2. **Load the report.** Read `.local/ASSESSMENT.md`. If missing, report that
   and stop.
3. **Resolve targets** from `$ARGUMENTS` per **Target selection**. Zero
   matches → report and stop.
4. **Check sizing.** Every target must carry a `**Suggested Model/Effort:**`
   line. If any is missing, stop and tell the operator to run
   `/review-triage .local/ASSESSMENT.md` first. Do not guess a default — an
   unsized finding may be a hidden bug.
5. **Resolve the verify gate** per **Verify gate**; you will state the
   resolved commands in the final report and embed them verbatim in every
   subagent prompt.
6. **Gather project conventions.** Read `AGENTS.md`/`CLAUDE.md` once; the
   repo-specific conventions you find (uniformity across sibling packages,
   doc/env pairing, mock/stub sync, comment style, deprecation policy) go
   verbatim into every subagent prompt.
7. **Pick the mode.** If `.local/ASSESSMENT.TRIAGE.md` exists and the target
   set is exactly one of its batches or a union of whole batches → **batch
   mode**, processing batches in triage-file order (already risk-ordered; do
   not re-sort). Otherwise → **per-finding mode**, ordered Critical → Warning
   → Note; if a triage file exists but was bypassed, say so in the final
   report. If the triage file's finding count doesn't match the report's open
   findings, report the mismatch (informational, not a stop).
8. **Process targets** with the per-batch or per-finding procedure below.
9. **Finish** per **Final report**; keep **Commit message** current as you go.

## Operating rules (non-negotiable)

- **The report is a lead, not a mandate.** Every `Fix` block — and any
  `Codex Evaluation`/`Codex Suggested Fix` content — is an unverified
  proposal. Subagents must check it against the nearest ADR under
  `docs/decisions/` and the touched function/type's doc comment before
  applying, per "a fix is a comment until proven otherwise."
- **ADR-amendment findings are not comment fixes.** A fix that requires
  *editing* a file under `docs/decisions/` (not just citing one) is a
  governance change: always `Requires checkpoint: yes` regardless of the
  triage file — get explicit operator sign-off on the ADR wording before
  writing it, and prefer the `/adr` skill's conventions for the edit when
  available.
- **Smallest correct change.** No drive-by refactors, formatting passes, or
  file moves.
- **No git, no worktree isolation.** Never branch, stage, or commit —
  subagents included. Never launch a fix subagent with `isolation:
  "worktree"`; it must edit the real working tree. Leave the tree dirty for
  the operator; the ASSESSMENT.md diff plus the code diff are the audit trail.
- **Stop on first failure.** Any verify-gate failure — whether hit by a
  subagent or by your own re-validation — or an impact radius too large to
  cover safely ends the whole run: report what failed with output, leave all
  work in place (do not revert), do not touch remaining targets.
- **Fix-accuracy tier rule.** When a proposed fix is wrong, unsafe, or
  incomplete: **Haiku/Low** findings — the subagent auto-corrects when the
  correction is still small (apply it, note the deviation); any finding that
  **escalates to a real behavior fix**, regardless of original tier — the
  subagent stops without applying anything and reports the problem plus a
  proposed correction, which you present to the operator (accept / reject =
  hard stop / supply a different fix). **Clean-slate restart:** an accepted
  alternative gets a brand-new subagent (fresh `Agent` call, same — or
  escalated — model/effort) with the accepted fix substituted for the
  report's original; never resume the rejected subagent.
- **Graph first.** Subagents must use the `code-review-graph` MCP tools
  (`semantic_search_nodes`, `query_graph`, `get_impact_radius`,
  `get_affected_flows`) before Grep/Read, per `CLAUDE.md`; if unavailable,
  trace callers/dependents manually.

## Target selection

Parse `$ARGUMENTS` case-insensitively. Ignore filler words (`all`, `and`,
`for`, `the`, commas). Tokens are **severities** (`critical`, `warning`,
`note`) or **finding IDs** matching `#[A-Z0-9]+-[A-Z0-9]+-\d+`.

1. **Inclusion:** no tokens or `all` alone → every open finding; severities →
   findings of those severities; IDs → exactly those findings (union with any
   severities also present).
2. **Exclusion:** tokens after `except`, `except for`, or `but not` are
   removed from the inclusion set.
3. Targets = inclusion − exclusion, ordered Critical → Warning → Note.

| Invocation | Targets |
| --- | --- |
| `/assessment-fix` | every open finding |
| `/assessment-fix critical` | all Critical findings |
| `/assessment-fix warning and note` | all Warning + Note findings |
| `/assessment-fix #CFG-CNTR-23` | only `#CFG-CNTR-23` |
| `/assessment-fix all except #SU-CNTR-64` | everything but `#SU-CNTR-64` |

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
| Low | "Apply the described fix directly once you've confirmed it's correct and re-derived any numeric/formula rationale it asserts. Keep the regression-guard graph check brief." |
| Medium | "Verify assumptions with the graph tools before applying the fix; re-derive it if gaps appear. Check at least one layer of callers/dependents via `get_impact_radius`." |
| High | "Thoroughly investigate the impact radius and affected flows before applying anything. If the fix turns out to describe a real bug rather than an undocumented-but-correct value, stop and report it — do not write a confident-sounding comment for a value you can't verify." |

## Verify gate

Resolve once at the start of the run:

1. Commands defined in `AGENTS.md`/`CLAUDE.md` or the Makefile win.
2. Go fallback: **build+vet** = `go build ./...` + `go vet ./...`; **scoped
   lint** = `golangci-lint run --new-from-rev=$(git merge-base HEAD main)`;
   **full tests** = `make test` (or `go test ./...` if no Makefile).
3. Other languages: the equivalent compile/lint check and full test command.

Comment/doc-only fixes need only build+vet (this command's lighter gate); any
real code change also needs the scoped lint and full tests.

## Subagent prompt (used by both procedures)

Every fix subagent runs `subagent_type: "general-purpose"`, the resolved
`model`, no `isolation`, `run_in_background: false` (the next target must not
start until this one's outcome is known). The prompt must be fully
self-contained — the subagent starts cold — and include:

- The finding's full block from the report (ID, severity, Lines, Problem,
  Suggested Model/Effort, Fix, any Codex content). In batch mode: every
  finding in the batch.
- The effort instruction from the table above.
- The Operating rules verbatim: report-is-a-lead, the ADR-amendment rule,
  smallest correct change, no git/branch/commit, graph-first, the project
  conventions from playbook step 6, and the fix-accuracy tier rule.
- The task sequence, per finding:
  1. Re-validate the gap and proposed fix against current source (line
     numbers may have drifted; locate the real symbol via the graph tools).
  2. **Re-derive, don't transcribe**, any rationale the fix asserts for a
     numeric constant, formula, or derived value. If it doesn't hold up,
     stop that finding and report it as a likely real bug — never fall
     through to applying a plausible-sounding comment anyway.
  3. Regression guard: `get_impact_radius` + `get_affected_flows` on the
     symbols to change; if the blast radius is larger than the fix can safely
     cover, stop and report instead of applying.
  4. Apply the fix (comment/doc change, or the small structural cleanup
     described). Only if it is a real behavior change — declared by the
     report or escalated by step 2 — add a regression test that fails on
     pre-fix behavior and passes after.
  5. Sync documentation as needed: doc comments, `README.md`, `AGENTS.md`,
     relevant ADRs, `docs/openapi.yaml`, `.env.example` + `README.md`
     together for flag/env changes. Markdown stays lint-clean per `CLAUDE.md`.
  6. Run the verify gate (commands embedded verbatim): build+vet always; the
     scoped lint and full tests only if any real code change was made. In
     batch mode the gate runs once for the whole batch.
- Reporting requirements: files changed, the regression test name (or
  "none — comment-only fix"), docs touched, exact gate commands run with
  pass/fail output, and — if it stopped — exactly why.

## Per-finding procedure

1. **Staleness check (you, no subagent).** Grep/read the cited file: does the
   gap still plausibly exist? Clearly already resolved → remove the finding
   from the report (step 4) with a note "already fixed" and move on.
2. **Dispatch** one subagent per **Subagent prompt**.
3. **Handle the outcome.**
   - Success → step 4's validation.
   - Stopped on oversized impact radius or a gate failure → hard stop for the
     run (Operating rules).
   - Stopped on an escalation to a real bug, or a tier-rule rejection →
     present the proposal to the operator; on acceptance do a clean-slate
     restart at step 2, upgrading model/effort per the escalation.
4. **Independent validation, then accept.** Never accept on the subagent's
   self-report:
   - **Re-derive any constant/formula rationale yourself, again**, even
     though the subagent claims it did (delegate to an `opus` subagent if
     nontrivial) — this is the primary check for this command. A value that
     doesn't hold up is a real bug: leave the finding open, report the
     discrepancy, and propose re-sizing (Sonnet/High or higher, code fix +
     test) for a follow-up.
   - Re-run build+vet; if any real code change was made, also re-run the
     regression test, the full test command, and the scoped lint.
   - Any failure or discrepancy = verify-gate failure = hard stop.
   - On pass: delete the finding's section and Finding Index row from
     `.local/ASSESSMENT.md` (and the now-empty file heading, if last); remove
     or narrow any triage-file reference; keep the report lint-clean; update
     the commit message; next target.

## Per-batch procedure (batch mode)

1. **Load the batch** from the triage file (IDs, files, `Requires
   checkpoint`) and each finding's full block from the report. If `Requires
   checkpoint: yes`, **or the batch's fix touches `docs/decisions/`**
   (ADR-amendment rule): present the finding(s) and fix to the operator and
   get explicit approval first — silence is not approval.
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
   - **Re-derive** every constant/formula rationale in the batch yourself,
     again (delegate to `opus` if nontrivial); a failure is a tier-rule
     failure for that finding — leave it open and propose re-sizing.
   - Re-run build+vet once for the batch; if any finding required a real
     code change, also re-run its test, the full test command, and the
     scoped lint, and confirm the new test is present and passing.
   - Any gate failure or unresolved discrepancy → hard stop for the run.
5. **Accept:** for each finding that passed, delete its section and index row
   from `.local/ASSESSMENT.md`; remove or narrow the batch's entry in
   `.local/ASSESSMENT.TRIAGE.md`; update the commit message; next batch.

## Codex handoff and resume

**Handoff (dispatching a Codex batch):** write `.local/CODEX-PROMPT.md` — a
self-contained prompt listing every finding's ID, file, Problem, and Fix,
with explicit constraints: only the batch's named files, comment/fix content
only as specified, no reformatting beyond the fix, no commit, no build/test
run (validation happens here on resume). Report which batch it is and that
this run is stopping; the next `/assessment-fix` invocation resumes
automatically. This is a soft stop, not a failure.

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
  added (or "comment-only"), docs updated (grouped by batch in batch mode).
- **Escalated to bug fixes:** any finding where re-derivation revealed a real
  bug — the original finding, what was actually wrong, and the fix applied.
- **Auto-corrected (Low):** report proposal vs. what was applied and why.
- **Skipped (already fixed)** and **Skipped (unaddressed in batch)** — the
  latter still open, needs a follow-up run.
- **Awaiting Codex:** if stopped after writing `.local/CODEX-PROMPT.md`.
- **Stopped at:** the finding/batch, which gate or step failed, the output
  or corrected proposal, and the recommended next action.
- **Remaining:** open findings still in `.local/ASSESSMENT.md`.
- The resolved verify-gate commands, and confirmation that
  `.local/COMMIT-MSG.txt` is current.
- Remind the operator the tree is **dirty and uncommitted** — review the
  report diff and code diff, then commit when satisfied.

## Commit message

Immediately after each finding/batch is accepted — not only at the end, so a
mid-run stop leaves an accurate partial draft — upsert
`.local/COMMIT-MSG.txt` (a file write, exempt from the no-git rule):

- **Create** (if absent): a conventional-commit subject summarizing the run
  (e.g. `docs: close N comprehensibility findings`), a blank line, one bullet
  per accepted finding. No `Co-Authored-By:` trailer — never add one.
- **Append** (if present): read it first; leave the existing subject and
  bullets untouched; add one bullet per newly accepted finding; never
  duplicate an ID already listed.
- **Bullet:** `- <ID> (<file>): <one clause — what changed and why>.` Note
  briefly if auto-corrected or escalated from a doc gap to a real bug fix.
- Skip findings removed only by a staleness check — nothing changed this run.
