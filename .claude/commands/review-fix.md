---
description: Fix open findings from .local/REVIEW.md via sized subagents, each verified before removal from the report
argument-hint: [filter]
---

<!-- Keep the shared mechanics (Target selection, Model/effort resolution,
Execution mode, Codex handoff/resume, Commit message) in sync with
assessment-fix.md — the two files are deliberately parallel. -->

# /review-fix

Fix findings recorded in `.local/REVIEW.md`, each fully validated,
regression-guarded, tested, and documented before it is accepted and removed
from the report. Each fix is performed by a dedicated subagent launched at
the model/effort the finding calls for; the orchestrator (you) independently
re-validates the subagent's work before accepting it.

If `.local/REVIEW.TRIAGE.md` exists (produced by `/review-triage`) and the
resolved target set is a whole batch or union of batches from it, findings
are processed **batch by batch** — one dispatch and one verify gate per
batch — instead of one at a time. See **Execution mode** below. Without a
triage file, or when the target set cuts across a batch, findings are
processed one at a time as described in **Per-finding procedure**.

Arguments: `$ARGUMENTS` (a filter selecting which findings to fix; see **Target
selection**). When empty, every open finding is targeted.

---

## Operating rules (non-negotiable)

- **Source of truth.** `.local/REVIEW.md` lists the open findings. `AGENTS.md`
  governs validation, Definition of Done, and documentation sync; obey it.
- **Smallest correct change.** Apply the fix in the finding (or a corrected
  version of it — see step 3), nothing more. No drive-by refactors, no
  formatting passes, no file moves.
- **The report is a lead, not a mandate.** Treat every `Fix` block — and any
  `Codex Evaluation`/`Codex Suggested Fix` content appended to it — as an
  unverified proposal. Fix subagents must independently check it against the
  nearest ADR under `docs/decisions/` and the touched function/type's doc
  comment before applying, because a report can be stale, wrong, or written by
  an agent that skipped that check. A fix that is small but contradicts
  governing intent is not minimal — it is wrong, and is handled by the
  fix-accuracy tier rule below like any other wrong fix.
- **No git, no worktree isolation.** Never branch, stage, or commit — this
  applies to subagents too. Do not launch fix subagents with `isolation:
  "worktree"`; they must edit the real, shared working tree so the operator sees
  one dirty tree at the end, not a stray branch. Leave the working tree dirty
  for the operator to review and commit. The REVIEW.md diff plus the code diff
  are the audit trail.
- **Stop on first failure.** Process targets in severity order (Critical → High
  → Medium → Low). On any **verify-gate** failure (build, vet, lint, tests) —
  whether caught by the fix subagent or by the orchestrator's independent
  re-validation in step 5 — or an impact radius too large to cover safely,
  **stop**: report what failed with output, leave all work in place (do not
  revert), and do not touch the remaining findings. Fix-*accuracy* problems
  follow the **tier rule** (step 3), not this hard stop.
- **Fix-accuracy tier rule.** When the report's proposed fix is wrong, unsafe, or
  incomplete: **Low** findings are auto-corrected by the fix subagent itself
  (apply the smallest correct fix and note the deviation); **Medium / High /
  Critical** findings make the fix subagent stop without applying anything and
  report the problem plus a proposed correction back to you, so you can ask the
  operator. An accepted alternative gets a **brand-new fix subagent** — see
  **Clean-slate restart** in step 4. Full mechanics in step 3.
- **Graph first.** When the project has a `code-review-graph` knowledge graph,
  fix subagents must use its MCP tools (`semantic_search_nodes`, `query_graph`,
  `get_impact_radius`, `get_affected_flows`) before Grep/Read, per `CLAUDE.md`.
  If the graph tools are unavailable, trace callers/dependents manually instead —
  the regression-guard step still applies.
- **Project conventions.** Read the repo's `AGENTS.md`/`CLAUDE.md` for
  repo-specific conventions (uniformity rules across sibling binaries or
  packages, doc/env-file pairing, mock/stub sync rules, comment style,
  deprecation policy) and include the relevant ones verbatim in every fix
  subagent prompt. Repo-specific rules live in the repo, not in this command.

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

## Model/effort resolution

Each finding block may carry a line of the form:

```text
**Suggested Model/Effort:** <Model> / <Effort> — <reasoning>
```

Parse `<Model>` and `<Effort>` from this line before dispatching the fix
subagent (step 3).

**Model → Agent tool `model` param:**

| Suggested Model | `model` value | Notes |
| --- | --- | --- |
| Haiku | `haiku` | |
| Sonnet | `sonnet` | |
| Opus | `opus` | |
| Codex | *(none)* | Not launched via the Agent tool — Codex is a different vendor's CLI, external to this session. Handled by the **Codex handoff** procedure instead: write a self-contained prompt file, stop, and resume when the operator reports the external run is done. See **Execution mode** below. |
| *(line absent)* | `sonnet` | Should not occur if `/review-triage` has run (it backfills this field). If it does anyway, default to `sonnet` and note in the final report that a default was applied. |

**Effort → prompt instruction** (the Agent tool has no effort parameter; effort
is conveyed as explicit prose in the subagent's prompt):

| Effort | Instruction embedded in the subagent prompt |
| --- | --- |
| Low | "Apply the described fix directly once you've confirmed it's correct. Keep the regression-guard graph check brief — the directly impacted symbol is enough." |
| Medium | "Verify assumptions with the graph tools before applying the fix; re-derive it if gaps appear. Check at least one layer of callers/dependents via `get_impact_radius`." |
| High | "Thoroughly investigate the impact radius and affected flows before applying anything. Reason carefully through concurrency/design implications and edge cases, and make sure the regression test actually exercises them." |

---

## Verify gate

The verify gate is the project's build + vet/lint + test commands, resolved once
at the start of the run and used everywhere this file says "verify gate":

1. If `AGENTS.md`/`CLAUDE.md` or the Makefile defines build/lint/test commands,
   use those.
2. Otherwise, for Go projects default to: `go build ./...`, `go vet ./...`,
   `golangci-lint run --new-from-rev=$(git merge-base HEAD main)` (scoped lint —
   new issues only), and `make test` (or `go test ./...` if no Makefile).
3. For other languages, substitute the equivalent build, lint, and full-test
   commands (e.g. `npm run build` / `npm run lint` / `npm test`).

State the resolved commands in the final report. Include them verbatim in every
fix subagent prompt.

---

## Execution mode

Determine mode once, before processing any targets, after Target selection
has produced the final ID set.

1. If `.local/REVIEW.TRIAGE.md` does not exist → **per-finding mode**.
2. If it exists, load its batches. Check whether the final target ID set is
   exactly one batch, or the exact union of two or more whole batches.
   - Yes → **batch mode**, processing the matched batches in the order they
     appear in the triage file (which is already risk-ordered — do not
     re-sort).
   - No (the target set splits a batch, or includes findings the triage file
     doesn't know about) → **per-finding mode**, and note in the final report
     that the triage file exists but was bypassed because the filter cut
     across a batch boundary; suggest re-running `/review-triage` if the
     source report has changed since it was generated.
3. Regardless of mode, if the triage file's total finding count doesn't match
   the number of open findings in `.local/REVIEW.md`, report the mismatch
   before proceeding (new findings may have been added since triage ran) —
   this is informational, not a stop condition, unless it also affects step 2's
   batch-matching, in which case per-finding mode already handles it.

### Resuming after a Codex batch

Before doing anything else, check whether `.local/CODEX-PROMPT.md` exists.
Its presence means a previous `/review-fix` run stopped mid-batch waiting on
an external Codex run.

- Read the batch's finding list back out of `.local/CODEX-PROMPT.md` (it
  names the target files and finding IDs). Check `git diff` / `git status`
  for those files.
- **No changes to those files yet** → the external run hasn't happened or
  hasn't finished. Report this and stop; do not proceed to any other target.
- **Changes present** → treat this invocation as a resume: skip straight to
  **Post-batch validation** for that batch (below), using the diff as the
  "subagent's" output. Once that batch is accepted or resolved, delete
  `.local/CODEX-PROMPT.md` and continue with the next batch/target in the
  normal order.

---

## Per-batch procedure (batch mode only)

Run these steps in order for one batch. A **STOP** condition ends the whole
`/review-fix` run for hard stops, or just this batch for soft stops — each
step below says which.

### B1. Load the batch

Read the batch's finding IDs, files, and `Requires checkpoint` flag from the
triage file. Read each finding's full block from `.local/REVIEW.md` (ID,
severity, `Line(s)`, Issue, Scope, Suggested Model/Effort, Fix, Rationale,
Test, and any `Codex Evaluation`/`Codex Suggested Fix` content).

If `Requires checkpoint: yes` — this should only occur on size-1 batches
(triage never bundles a checkpoint item with anything else). Present the
finding and its proposed fix to the operator and get explicit approval
before proceeding to B2. Treat silence or an unrelated reply as "not yet
approved" — do not proceed.

### B2. Quick staleness check (orchestrator, no subagent)

For each finding in the batch, do a cheap check yourself (grep/read) that
the described defect still plausibly exists. Drop any finding that's
already resolved from this batch's working set (remove from REVIEW.md per
step B6 immediately, no subagent needed for it). If the whole batch turns up
already-resolved, skip to B6 and move on — no dispatch needed.

### B3. Dispatch

**If the batch's model is Haiku, Sonnet, or Opus:** launch one `Agent` call
covering the entire batch (not one call per finding). The prompt must be
fully self-contained and include, for every finding in the batch: its full
content from B1, the effort instruction for the batch's tier (see
**Model/effort resolution**), the relevant Operating rules verbatim (smallest
correct change per finding, no git/branching/committing, graph-first tool
usage, the project conventions gathered from `AGENTS.md`/`CLAUDE.md`,
fix-accuracy tier rule), and instructions
to, per finding: re-validate against current source (checking the fix and any
appended Codex content against the nearest ADR and the touched doc comment,
per the fix-accuracy tier rule), check impact radius, apply the fix (or the
tier-rule correction), add/update a regression test, and sync documentation.
Then, **once for the whole batch**: run the verify gate (see **Verify gate**;
include the resolved commands verbatim in the prompt) and report back
per-finding outcomes plus the single verify-gate result.

**If the batch's model is Codex:** do not dispatch an Agent. Instead:

1. Write `.local/CODEX-PROMPT.md`: a self-contained prompt listing every
   finding's ID, file, Problem/Issue, and Fix content, with explicit
   constraints (only the batch's named files, comment/fix content only as
   specified, no reformatting beyond what the fix requires, no commit, no
   build/test run — those happen here after review).
2. Report to the operator: which batch this is, that
   `.local/CODEX-PROMPT.md` is ready to hand to Codex, and that this run is
   stopping here. **STOP** (soft — this ends the current invocation, not a
   failure; the next `/review-fix` invocation resumes via **Resuming after a
   Codex batch** above).

### B4. Handle the dispatch outcome

Same **Handle the subagent's outcome** rules as per-finding mode (below),
applied once for the batch's Agent-tool outcome, or via the resume path for
a Codex batch.

### B5. Post-batch validation (orchestrator-owned)

Do not accept a batch on the subagent's self-report, or on the presence of a
diff from an external Codex run, alone.

1. **Reconcile applied-vs-requested.** For each finding ID in the batch,
   confirm the diff actually touches that finding's file/location. Any
   finding with no evidence of being addressed is a **soft stop for that
   finding only**: do not remove it from `.local/REVIEW.md` or the triage
   file's batch entry, note it explicitly in the final report (ID, why it
   looks unaddressed), and continue validating the rest of the batch — do
   not guess at applying it yourself here, and do not silently drop it from
   tracking.
2. **Re-derive, don't trust, constant-explaining fixes.** For any finding in
   the batch whose fix asserts a rationale for a magic number, formula, or
   derived value, independently re-derive that value from the code it
   describes before accepting the fix as correct — do not accept a
   plausible-sounding comment on faith. If it doesn't hold up, treat this
   exactly like a fix-accuracy tier-rule failure for that finding (Low:
   correct it yourself if it's still a small change; Medium+: stop that
   finding and report the discrepancy as a real bug, not a doc gap — it may
   need re-sizing and a code fix with a test, not a comment).
3. Re-run, yourself, every new/updated test named across the batch.
4. Re-run the verify gate's full test command once for the batch.
5. Re-run the verify gate's build, vet, and scoped lint commands once for
   the batch, unless every finding in it is a pure comment/doc change with no
   compiled-code impact (then build/vet alone is sufficient).

Any gate failure or unresolved reconciliation-worthy discrepancy from step 1
or 2 that can't be resolved as described is treated like a verify-gate
failure under Operating rules for **that batch**: stop processing further
targets, report the batch, the specific finding(s), and the failing output;
leave work in place.

### B6. Accept and remove from the report

For each finding in the batch that passed B5 cleanly: delete its section and
Finding Index row from `.local/REVIEW.md` per step 6 of the per-finding
procedure below. Remove the batch's entry from the triage file, or narrow it
to just the finding(s) still open per step B5.1. Move to the next
batch/target.

---

## Per-finding procedure

Run these steps in order for one finding. Any **STOP** condition ends the whole
command (stop on first failure).

### 1. Load the finding

Read the finding's full block from `.local/REVIEW.md`: ID, severity, file,
`Line(s)`, Issue, Fix, Rationale, and any `Codex Evaluation` / `Codex Suggested
Fix` content present. Parse the `Suggested Model/Effort` line per **Model/effort
resolution** above.

### 2. Quick staleness check (orchestrator, no subagent)

Before spending a subagent call, do a cheap check yourself: open the cited file
and confirm the described defect still plausibly exists (a grep/read is
enough — full re-validation of fix *correctness* is the subagent's job in step
3, not yours here).

- If the defect is **clearly already resolved** → remove the finding from
  REVIEW.md (step 6 cleanup) with a note "already fixed", and continue to the
  next target. No subagent is dispatched for this finding.
- Otherwise, proceed to step 3.

### 3. Dispatch the fix subagent

Launch one `Agent` call with:

- `subagent_type: "general-purpose"` (needs Bash/Read/Edit/Write plus the
  `code-review-graph` MCP tools).
- `model`: the value resolved in **Model/effort resolution**.
- No `isolation` parameter (must edit the real working tree — see Operating
  rules).
- `run_in_background`: unset (run in the foreground) — the next finding must
  not start until this one's outcome is known, per "stop on first failure".

The prompt must be fully self-contained (the subagent starts cold with no
memory of this conversation) and must include:

- The finding's full content from step 1 (ID, severity, file, line(s), issue,
  fix, rationale, and any Codex evaluation/suggested fix).
- The effort instruction resolved above.
- The relevant Operating rules verbatim: smallest correct change, no git/no
  branching/no committing, graph-first tool usage, the project conventions
  gathered from `AGENTS.md`/`CLAUDE.md`, and the **fix-accuracy tier rule**
  (verbatim, including the Low auto-correct/non-trivial-exception and the
  Medium+ stop-without-applying behavior).
- Instructions to perform, in order, what were originally steps 2–6 of this
  procedure:
  1. Re-validate the defect and the proposed fix against current source (line
     numbers may have drifted; locate the real symbol via the graph tools).
     Re-deriving correctness includes checking the fix — and any appended
     `Codex Evaluation`/`Codex Suggested Fix` — against the nearest ADR under
     `docs/decisions/` and the touched function/type's doc comment; a fix that
     is small but contradicts either counts as "wrong" for step 3 below, not
     as pre-approved because it's written down.
  2. Regression guard: run `get_impact_radius` and `get_affected_flows` on the
     symbol(s)/file(s) to change; if the blast radius is larger than the fix can
     safely cover, stop and report instead of applying.
  3. Apply the smallest correct fix (or the tier-rule-corrected fix for Low
     findings; for Medium/High/Critical findings with a wrong/unsafe/incomplete
     proposed fix — including one that violates governing intent per step 1 —
     **stop without applying anything** and report the problem plus a
     proposed correction).
  4. Add or update a regression test that fails on the pre-fix behavior and
     passes after; update any mirrored mock/stub types in the same pass.
  5. Sync documentation: doc comments for any changed contract, external
     markdown (`README.md`, `AGENTS.md`, relevant ADRs, `docs/openapi.yaml`) if
     behavior or an API contract changed, and `.env.example`/`README.md`
     together for any flag/env change. Keep markdown lint-clean per `CLAUDE.md`.
  6. Run the **verify gate** itself before reporting back (the resolved
     commands, included verbatim in this prompt), and confirm the new/updated
     test is included and passing.
- Instructions to report back precisely: what was changed (files + a diff
  summary), the regression test added/updated and its name, docs touched, the
  exact verify-gate commands run and their pass/fail output, and — if it
  stopped — exactly why (oversized impact radius, tier-rule Medium+ rejection
  with proposed correction, or a gate failure) with no changes left applied in
  the stop case.

### 4. Handle the subagent's outcome

- **Success reported** → proceed to step 5 (independent validation). Do not
  yet touch REVIEW.md.
- **Stopped: oversized impact radius, or a verify-gate failure** → this is a
  hard stop for the whole `/review-fix` run. Report the finding ID, what the
  subagent found, and the failing output. Leave all work as the subagent left
  it (do not revert). Do not process remaining targets.
- **Stopped: Medium/High/Critical tier-rule rejection** → present the
  subagent's explanation and proposed correction to the operator and ask
  whether to accept it, reject it (hard stop, same as above), or supply a
  different fix.
  - **Clean-slate restart:** if the operator accepts a proposal (the
    subagent's or their own), do **not** resume the same subagent or reuse its
    context. Dispatch a **brand-new** fix subagent (fresh `Agent` call, same
    model/effort resolution) for this finding, re-entering this procedure at
    step 3 with the accepted fix substituted for the report's original `Fix`.
    A fresh subagent naturally enforces "clean slate" — it re-derives
    everything from source with no reliance on the prior (rejected) analysis.

### 5. Independent post-subagent validation (orchestrator-owned)

Do not accept a finding on the subagent's self-report alone. After a subagent
reports success:

1. If the fix asserts a rationale for a magic number, formula, or derived
   value, independently re-derive that value from the code it describes
   before accepting the fix — do not accept a plausible-sounding comment on
   faith. If it doesn't hold up, this is a fix-accuracy tier-rule failure:
   the "doc gap" may actually be a real bug that needs re-sizing and a code
   fix with a test, not a comment.
2. Re-run, yourself, the specific new/updated test(s) it named.
3. Re-run the verify gate's full test command.
4. If the touched files could plausibly affect build/vet/lint scope beyond the
   named test (i.e. almost always), also re-run the verify gate's build, vet,
   and scoped lint commands.

Any failure or discrepancy from what the subagent reported is treated exactly
like a verify-gate failure under Operating rules: **STOP**, report the command
and its output, leave work in place, do not touch the remaining findings.

### 6. Accept and remove from the report

Only after independent validation (step 5) passes:

- Delete the finding's entire per-file section from `.local/REVIEW.md`.
- Delete its row from the **Finding Index** table.
- If that was the last finding under a `### path/to/file` heading, remove the now-empty heading block.
- Keep `.local/REVIEW.md` lint-clean and internally consistent.

Do **not** commit. Move to the next target.

---

## Final report

After the run (whether it completed or stopped early), print a concise summary:

- **Mode:** per-finding or batch, and (if batch) which batches from
  `.local/REVIEW.TRIAGE.md` were in scope this run.
- **Fixed:** for each accepted finding — ID, model/effort used (and any
  missing-field→Sonnet/Medium substitution applied), files touched, test
  added, docs updated. Group by batch in batch mode.
- **Auto-corrected (Low):** any Low finding where the fix subagent applied a
  fix that differed from the report — note the report's proposal vs. what was
  applied and why.
- **Skipped (already fixed):** any findings a staleness check found already
  resolved.
- **Skipped (unaddressed in batch):** any finding B5.1 found with no evidence
  of being addressed — still open in the report, needs a follow-up run.
- **Awaiting Codex:** if this run stopped after writing
  `.local/CODEX-PROMPT.md` — which batch, and that the next `/review-fix`
  invocation resumes automatically once the operator reports the external
  run is done.
- **Stopped at:** if halted — the finding ID or batch, the gate/step that
  failed (fix subagent's verify gate, orchestrator's independent
  re-validation, oversized impact, a Medium+ proposed-fix rejection, or a
  batch reconciliation/constant-re-derivation discrepancy), the failing
  output or the corrected proposal, and the recommended next action.
- **Remaining:** open findings still in `.local/REVIEW.md`.
- **Commit message:** confirm `.local/COMMIT-MSG.txt` was created or updated
  with an entry for each finding accepted this run (see **Commit message**
  below).
- Remind the operator: the working tree is **dirty and uncommitted** — review the
  `.local/REVIEW.md` diff and the code diff, then commit when satisfied.

---

## Commit message

Immediately after each finding/batch is accepted (step 6 / B6) — not only at
the very end, so a mid-run stop still leaves an accurate partial draft —
upsert `.local/COMMIT-MSG.txt`, a plain-text git commit message body the
operator will use for the eventual commit. This is a file write, not a git
operation, so it is exempt from the "no git" rule.

- **If the file doesn't exist**, create it: a one-line conventional-commit
  subject summarizing the run so far (e.g. `fix: resolve N review findings
  from batch <range>`), a blank line, then one bullet per accepted finding.
  No `Co-Authored-By:` trailer — do not add one.
- **If it already exists** (uncommitted fixes from an earlier run this
  session), read it first. Leave its existing subject line and bullets
  untouched; append one new bullet per finding accepted in *this* run, same
  format, at the end of the file. Never duplicate a bullet for a finding ID
  already listed — check by ID before appending.
- **Bullet format:** `- <ID> (<file>): <one clause — what changed and why>.`
  Name the regression test added/updated in the same clause when there is
  one (there almost always is for `/review-fix`, since findings are behavior
  defects). Note inline, briefly, if the finding was auto-corrected (Low
  tier). Keep it minimal — one clause, not a restatement of the Issue/Fix
  text; the report and the code diff are the full record, this is a commit
  draft.
- Skip this step for a finding removed only because the staleness check (B2
  / step 2) found it already fixed — nothing changed in this run, so there's
  nothing to add to the message.
