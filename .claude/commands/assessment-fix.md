---
description: Fix comprehensibility findings from .local/ASSESSMENT.md; re-derives asserted constants, lighter gate for doc-only fixes
argument-hint: [filter]
---

<!-- Keep the shared mechanics (Target selection, Model/effort resolution,
Execution mode, Codex handoff/resume, Commit message) in sync with
review-fix.md — the two files are deliberately parallel. -->

# /assessment-fix

Fix findings recorded in `.local/ASSESSMENT.md`, each independently
re-verified and documented before it is accepted and removed from the
report. Each fix is performed by a dedicated subagent launched at the
model/effort the finding calls for; the orchestrator (you) independently
re-validates the subagent's work before accepting it.

If `.local/ASSESSMENT.TRIAGE.md` exists (produced by `/review-triage`) and
the resolved target set is a whole batch or union of batches from it,
findings are processed **batch by batch** — one dispatch and one
verification pass per batch — instead of one at a time. See **Execution
mode** below. Without a triage file, or when the target set cuts across a
batch, findings are processed one at a time as described in **Per-finding
procedure**.

Arguments: `$ARGUMENTS` (a filter selecting which findings to fix; see
**Target selection**). When empty, every open finding is targeted.

---

## Why this command differs from `/review-fix`

`/review-fix` fixes bugs; every accepted fix gets a regression test almost
by definition, because the finding *is* a behavior defect. `/assessment-fix`
fixes comprehensibility gaps, and most of those fixes are pure documentation
— there is no behavior to regression-test against a comment. Forcing a test
requirement onto a doc-only fix would be busywork; skipping verification
entirely would be careless. The rule this command uses instead:

- **A fix is a comment until proven otherwise.** Before accepting any fix
  that explains a magic number, formula, derived value, or "why this and not
  that" rationale, independently re-derive it from the code it describes.
  Transcribing the report's proposed wording is not verification. This is
  how a "document the +6 constant" finding turned out to actually be a wrong
  constant (the rule under a table header was rendered 1 character short of
  the header itself) — the finding's Problem text described it as an
  undocumented-but-correct value, and it wasn't.
- **If re-derivation fails, the finding just got bigger.** A fix that turns
  out to describe a real bug is no longer comment-only — re-size it (at
  least Sonnet/High; use the sizing table in `/review-triage` as reference),
  require an actual code fix plus a regression test for it, same as
  `/review-fix` would demand, and say explicitly in the final report that
  this finding escalated from a doc gap to a bug fix and why.
- **Everything else — the common case — gets a lighter gate.** Build + vet
  (or the project's equivalent compile/lint check) is sufficient for a fix
  that only touches comments or doc strings. No test is invented for code
  that didn't change behavior.

---

## Operating rules (non-negotiable)

- **Source of truth.** `.local/ASSESSMENT.md` lists the open findings.
  `AGENTS.md` governs validation, Definition of Done, and documentation sync;
  obey it.
- **Smallest correct change.** Apply the fix in the finding (or a corrected
  version of it — see the fix-accuracy tier rule), nothing more. No drive-by
  refactors, no formatting passes, no file moves.
- **The report is a lead, not a mandate.** Treat every `Fix` block — and any
  `Codex Evaluation`/`Codex Suggested Fix` content appended to it — as an
  unverified proposal. Fix subagents must independently check it against the
  nearest ADR under `docs/decisions/` and the touched function/type's doc
  comment before applying, per the "fix is a comment until proven otherwise"
  rule above.
- **ADR-amendment findings are not comment fixes.** If a finding's proposed
  fix requires editing a file under `docs/decisions/` (not just citing one),
  that's a governance change, not documentation. These are always
  `Requires checkpoint: yes` regardless of what the triage file says — get
  explicit operator sign-off on the ADR wording before writing it, and
  prefer invoking the `/adr` skill's conventions for the edit itself if one
  is available in this session.
- **No git, no worktree isolation.** Never branch, stage, or commit — this
  applies to subagents too. Do not launch fix subagents with `isolation:
  "worktree"`. Leave the working tree dirty for the operator to review and
  commit. The `ASSESSMENT.md` diff plus the code diff are the audit trail.
- **Stop on first failure.** Process targets in severity order (Critical →
  Warning → Note), or in triage batch order if in batch mode. On any
  **verify-gate** failure, or an impact radius too large to cover safely,
  **stop**: report what failed with output, leave all work in place (do not
  revert), and do not touch the remaining findings.
- **Fix-accuracy tier rule.** When the report's proposed fix is wrong,
  unsafe, incomplete, or (per the rule above) turns out to describe a real
  bug: **Haiku/Low** findings are auto-corrected by the fix subagent itself
  when the correction is still small (apply it, note the deviation); any
  finding that escalates to a real behavior fix, regardless of its original
  tier, **stops without applying anything** and reports the problem plus a
  proposed correction back to you, so you can ask the operator. An accepted
  alternative gets a **brand-new fix subagent** — see **Clean-slate
  restart** in the per-finding procedure.
- **Graph first.** When the project has a `code-review-graph` knowledge graph,
  fix subagents must use its MCP tools (`semantic_search_nodes`, `query_graph`,
  `get_impact_radius`, `get_affected_flows`) before Grep/Read, per `CLAUDE.md`.
  If the graph tools are unavailable, trace callers/dependents manually
  instead.
- **Project conventions.** Read the repo's `AGENTS.md`/`CLAUDE.md` for
  repo-specific conventions (uniformity rules across sibling binaries or
  packages, doc/env-file pairing, mock/stub sync rules, comment style,
  deprecation policy) and include the relevant ones verbatim in every fix
  subagent prompt. Repo-specific rules live in the repo, not in this command.

---

## Target selection

Parse `$ARGUMENTS` case-insensitively. Ignore filler words (`all`, `and`,
`for`, `the`, commas). Tokens are either **severities** (`critical`,
`warning`, `note`) or **finding IDs** matching `#[A-Z0-9]+-[A-Z0-9]+-\d+`.

1. **Inclusion set:**
   - No severity/ID tokens, or the word `all` alone → every open finding.
   - One or more severities → all open findings of those severities.
   - One or more IDs → exactly those findings (ignore severity in this case
     unless severities are also present, in which case union them).
2. **Exclusion set:** tokens after `except`, `except for`, or `but not` are
   removed from the inclusion set (IDs or severities).
3. Final targets = inclusion − exclusion, ordered Critical → Warning → Note.

Examples:

| Invocation | Targets |
| --- | --- |
| `/assessment-fix` | every open finding |
| `/assessment-fix critical` | all Critical findings |
| `/assessment-fix warning and note` | all Warning + Note findings |
| `/assessment-fix #CFG-CNTR-23` | only `#CFG-CNTR-23` |
| `/assessment-fix all except #SU-CNTR-64` | everything but `#SU-CNTR-64` |

If `.local/ASSESSMENT.md` is missing, or the filter matches zero findings,
report that and stop without changing anything.

---

## Model/effort resolution

Each finding block carries a line of the form:

```text
**Suggested Model/Effort:** <Model> / <Effort> — <reasoning>
```

If it's absent, stop and tell the operator to run `/review-triage
.local/ASSESSMENT.md` first — this command requires the field to exist
(triage backfills it; guessing here risks under-sizing a finding this
command has no way to know is actually a hidden bug).

**Model → Agent tool `model` param:**

| Suggested Model | `model` value | Notes |
| --- | --- | --- |
| Haiku | `haiku` | |
| Sonnet | `sonnet` | |
| Opus | `opus` | |
| Codex | *(none)* | Not launched via the Agent tool. Handled by the **Codex handoff** procedure: write a self-contained prompt file, stop, and resume when the operator reports the external run is done. See **Execution mode** below. |

**Effort → prompt instruction:**

| Effort | Instruction embedded in the subagent prompt |
| --- | --- |
| Low | "Apply the described fix directly once you've confirmed it's correct and re-derived any numeric/formula rationale it asserts. Keep the regression-guard graph check brief." |
| Medium | "Verify assumptions with the graph tools before applying the fix; re-derive it if gaps appear. Check at least one layer of callers/dependents via `get_impact_radius`." |
| High | "Thoroughly investigate the impact radius and affected flows before applying anything. If the fix turns out to describe a real bug rather than an undocumented-but-correct value, stop and report it — do not write a confident-sounding comment for a value you can't verify." |

---

## Verify gate

Resolve the project's build + vet/lint + test commands once at the start of the
run and use them everywhere this file names a gate command:

1. If `AGENTS.md`/`CLAUDE.md` or the Makefile defines build/lint/test commands,
   use those.
2. Otherwise, for Go projects default to: **build+vet** = `go build ./...` +
   `go vet ./...`; **scoped lint** = `golangci-lint run
   --new-from-rev=$(git merge-base HEAD main)`; **full tests** = `make test`
   (or `go test ./...` if no Makefile).
3. For other languages, substitute the equivalent compile/lint check and full
   test command (e.g. `npm run build` / `npm run lint` / `npm test`).

Comment/doc-only fixes need only build+vet (this command's lighter gate); any
real code change needs the scoped lint and full tests as well. State the
resolved commands in the final report and include them verbatim in every fix
subagent prompt.

---

## Execution mode

Determine mode once, before processing any targets, after Target selection
has produced the final ID set.

1. If `.local/ASSESSMENT.TRIAGE.md` does not exist → **per-finding mode**.
2. If it exists, load its batches. Check whether the final target ID set is
   exactly one batch, or the exact union of two or more whole batches.
   - Yes → **batch mode**, processing the matched batches in the order they
     appear in the triage file (already risk-ordered — do not re-sort).
   - No → **per-finding mode**, and note in the final report that the
     triage file exists but was bypassed because the filter cut across a
     batch boundary.
3. If the triage file's total finding count doesn't match the number of
   open findings in `.local/ASSESSMENT.md`, report the mismatch before
   proceeding.

### Resuming after a Codex batch

Before doing anything else, check whether `.local/CODEX-PROMPT.md` exists.
Its presence means a previous `/assessment-fix` run stopped mid-batch
waiting on an external Codex run.

- Read the batch's finding list back out of `.local/CODEX-PROMPT.md`. Check
  `git diff` / `git status` for the files it names.
- **No changes yet** → the external run hasn't happened or hasn't finished.
  Report this and stop; do not proceed to any other target.
- **Changes present** → treat this invocation as a resume: skip straight to
  **Post-batch validation** for that batch, using the diff as the output to
  validate. Once that batch is accepted or resolved, delete
  `.local/CODEX-PROMPT.md` and continue with the next batch/target.

---

## Per-batch procedure (batch mode only)

### B1. Load the batch

Read the batch's finding IDs, files, and `Requires checkpoint` flag from the
triage file. Read each finding's full block from `.local/ASSESSMENT.md`
(ID, severity, `Lines`, Problem, Suggested Model/Effort, Fix, and any
`Codex Evaluation`/`Codex Suggested Fix` content).

If `Requires checkpoint: yes`, or the batch's fix touches `docs/decisions/`
(ADR-amendment rule above): present the finding(s) and proposed fix to the
operator and get explicit approval before proceeding to B2.

### B2. Quick staleness check (orchestrator, no subagent)

For each finding in the batch, do a cheap check yourself (grep/read) that
the described gap still plausibly exists. Drop any finding already resolved
from this batch's working set (remove per B6, no subagent needed). If the
whole batch is already resolved, skip to B6.

### B3. Dispatch

**If the batch's model is Haiku, Sonnet, or Opus:** launch one `Agent` call
covering the entire batch. The prompt must be fully self-contained and
include, for every finding: its full content from B1, the effort
instruction for the batch's tier, the relevant Operating rules verbatim
(smallest correct change, no git/branching/committing, graph-first tool
usage, the project conventions gathered from `AGENTS.md`/`CLAUDE.md`, the
ADR-amendment rule, the fix-accuracy tier rule), and instructions to, per
finding:

1. Re-validate against current source (line numbers may have drifted; locate
   the real symbol via the graph tools).
2. **Re-derive, don't transcribe**, any rationale the fix asserts for a
   numeric constant, formula, or derived value. If it doesn't hold up, stop
   that finding and report it as a likely real bug instead of applying the
   comment — do not fall through to applying a plausible-sounding fix anyway.
3. Check impact radius; apply the fix (comment/doc change, or the small
   structural cleanup described) if verification passed.
4. Only if the fix is a real behavior change (either the report already
   said so, or step 2 escalated it): add or update a regression test that
   fails on the pre-fix behavior and passes after.
5. Sync documentation: GoDoc for any changed contract, external markdown
   (`README.md`, `AGENTS.md`, relevant ADRs, `docs/openapi.yaml`) if the fix
   changed a documented contract, `.env.example`/`README.md` together for
   any flag/env change.

Then, **once for the whole batch**: run the verify gate's build+vet check
(the compile/lint check every finding needs). Additionally run the scoped
lint gate and the full test command only if any finding in the batch required
a real code change per step 4. Report back per-finding outcomes plus the gate
result(s).

**If the batch's model is Codex:** do not dispatch an Agent. Instead:

1. Write `.local/CODEX-PROMPT.md`: a self-contained prompt listing every
   finding's ID, file, Problem, and Fix content, with explicit constraints
   (only the batch's named files, comment/fix content only as specified, no
   reformatting beyond what the fix requires, no commit, no build/test run).
2. Report to the operator which batch this is, that
   `.local/CODEX-PROMPT.md` is ready to hand to Codex, and that this run is
   stopping here. **STOP** (soft — resumes on the next invocation per
   **Resuming after a Codex batch**).

### B4. Handle the dispatch outcome

- **Success reported** → proceed to B5. Do not yet touch `ASSESSMENT.md`.
- **Stopped: verify-gate failure, or a finding escalated to a real bug** →
  hard stop for the whole `/assessment-fix` run if it's a gate failure;
  otherwise present the escalation to the operator (accept the
  bug-fix-plus-test approach, reject, or supply a different fix) same as the
  fix-accuracy tier rule.

### B5. Post-batch validation (orchestrator-owned)

Do not accept a batch on the subagent's self-report, or on the presence of
an external Codex diff, alone.

1. **Reconcile applied-vs-requested.** For each finding ID in the batch,
   confirm the diff actually touches that finding's file/location. Any
   finding with no evidence of being addressed is a soft stop for that
   finding only: leave it open in `ASSESSMENT.md` and the triage batch, note
   it in the final report, and continue validating the rest of the batch.
2. **Re-derive, don't trust, constant-explaining fixes** — yourself, again,
   independent of whatever the subagent/Codex claimed. This is the primary
   check for this command; do not skip it because the subagent already
   claimed to have done it in step B3.2. If a fix doesn't hold up, treat it
   as a fix-accuracy tier-rule failure: report the discrepancy as a likely
   real bug, do not remove the finding from `ASSESSMENT.md`, and propose
   re-sizing it (Sonnet/High or higher, code fix + test) for a follow-up run.
3. The verify gate's build+vet check, once for the batch.
4. If any finding in the batch required a real code change (per B3 step 4),
   also re-run the scoped lint gate and the full test command once for the
   batch, and confirm the new/updated test is present and passing.

Any gate failure or unresolved discrepancy from step 1 or 2 stops processing
further targets; report the batch, the specific finding(s), and the output;
leave work in place.

### B6. Accept and remove from the report

For each finding in the batch that passed B5 cleanly:

- Delete its section and Finding Index row from `.local/ASSESSMENT.md`.
- If that was the last finding under a `### path/to/file` heading, remove
  the now-empty heading block.
- Remove the batch's entry from `.local/ASSESSMENT.TRIAGE.md`, or narrow it
  to just the finding(s) still open per B5.1.

Do **not** commit. Move to the next batch/target.

---

## Per-finding procedure (non-batch mode)

Run these steps in order for one finding. Any **STOP** condition ends the
whole command (stop on first failure), except a fix-accuracy escalation,
which is a soft stop for that finding only per the tier rule.

### 1. Load the finding

Read the finding's full block from `.local/ASSESSMENT.md`: ID, severity,
`Lines`, Problem, Suggested Model/Effort, Fix, and any `Codex Evaluation` /
`Codex Suggested Fix` content present. Parse the `Suggested Model/Effort`
line per **Model/effort resolution** above.

### 2. Quick staleness check (orchestrator, no subagent)

Open the cited file and confirm the described gap still plausibly exists.

- **Clearly already resolved** → remove the finding from `ASSESSMENT.md`
  (step 6 cleanup) with a note "already fixed", continue to the next target.
  No subagent dispatched.
- Otherwise, proceed to step 3.

### 3. Dispatch the fix subagent

Launch one `Agent` call with:

- `subagent_type: "general-purpose"`.
- `model`: the value resolved in **Model/effort resolution**.
- No `isolation` parameter.
- `run_in_background`: unset (foreground) — the next finding must not start
  until this one's outcome is known.

The prompt must be fully self-contained and include:

- The finding's full content from step 1.
- The effort instruction resolved above.
- The relevant Operating rules verbatim: smallest correct change, no
  git/branching/committing, graph-first tool usage, the project conventions
  gathered from `AGENTS.md`/`CLAUDE.md`, the ADR-amendment rule, and the
  fix-accuracy tier rule.
- Instructions to, in order:
  1. Re-validate the gap and the proposed fix against current source (line
     numbers may have drifted).
  2. **Re-derive, don't transcribe**, any rationale the fix asserts for a
     numeric constant, formula, or derived value. If it doesn't hold up,
     stop without applying anything and report it as a likely real bug.
  3. Regression guard: run `get_impact_radius` and `get_affected_flows` on
     the symbol(s)/file(s) to change; if the blast radius is larger than the
     fix can safely cover, stop and report instead of applying.
  4. Apply the fix (or the tier-rule-corrected fix). If the fix is a real
     behavior change, add or update a regression test that fails on the
     pre-fix behavior and passes after; if it's a pure comment/doc change,
     no test is needed.
  5. Sync documentation as needed (doc comments, README, ADRs, OpenAPI,
     `.env.example`).
  6. Run the verify gate (the resolved commands, included verbatim in this
     prompt): build+vet always; the scoped lint gate and the full test
     command only if step 4 required a real code change.
- Instructions to report back precisely: what was changed, the regression
  test added/updated (or "none — comment-only fix" if applicable), docs
  touched, the exact gate commands run and their pass/fail output, and — if
  it stopped — exactly why.

### 4. Handle the subagent's outcome

- **Success reported** → proceed to step 5. Do not yet touch `ASSESSMENT.md`.
- **Stopped: oversized impact radius, or a verify-gate failure** → hard stop
  for the whole `/assessment-fix` run. Report the finding ID, what the
  subagent found, and the failing output. Leave all work as the subagent
  left it. Do not process remaining targets.
- **Stopped: fix escalated to a real bug, or a tier-rule rejection** →
  present the subagent's explanation and proposed correction to the operator
  and ask whether to accept it, reject it (hard stop), or supply a different
  fix.
  - **Clean-slate restart:** if the operator accepts a proposal, dispatch a
    **brand-new** fix subagent (fresh `Agent` call, same model/effort
    resolution, or upgraded per the escalation) for this finding, re-entering
    this procedure at step 3 with the accepted fix substituted for the
    report's original `Fix`.

### 5. Independent post-subagent validation (orchestrator-owned)

Do not accept a finding on the subagent's self-report alone.

1. Independently re-derive any numeric/formula rationale the fix asserts —
   yourself, again, even though the subagent claims to have done this in
   step 3.2. This is the primary check for this command.
2. If a regression test was added, re-run it yourself; re-run the verify
   gate's full test command if any code change was made.
3. Re-run the verify gate's build+vet check; add the scoped lint gate if
   step 3.4 made a real code change.

Any failure or discrepancy is treated like a verify-gate failure under
Operating rules: **STOP**, report the command and its output, leave work in
place, do not touch the remaining findings.

### 6. Accept and remove from the report

Only after independent validation (step 5) passes:

- Delete the finding's entire per-file section from `.local/ASSESSMENT.md`.
- Delete its row from the **Finding Index** table.
- If that was the last finding under a `### path/to/file` heading, remove
  the now-empty heading block.
- If `.local/ASSESSMENT.TRIAGE.md` exists, remove or narrow its reference to
  this finding.
- Keep `.local/ASSESSMENT.md` lint-clean and internally consistent.

Do **not** commit. Move to the next target.

---

## Final report

After the run (whether it completed or stopped early), print a concise
summary:

- **Mode:** per-finding or batch, and (if batch) which batches from
  `.local/ASSESSMENT.TRIAGE.md` were in scope this run.
- **Fixed:** for each accepted finding — ID, model/effort used, files
  touched, whether a test was added (or "comment-only" if not), docs
  updated. Group by batch in batch mode.
- **Escalated to bug fixes:** any finding where constant re-derivation
  revealed a real bug instead of an undocumented-but-correct value — the
  original finding, what was actually wrong, and the fix applied.
- **Auto-corrected (Low):** any Low finding where the fix subagent applied a
  fix that differed from the report.
- **Skipped (already fixed):** any findings a staleness check found already
  resolved.
- **Skipped (unaddressed in batch):** any finding B5.1 found with no
  evidence of being addressed — still open, needs a follow-up run.
- **Awaiting Codex:** if this run stopped after writing
  `.local/CODEX-PROMPT.md` — which batch, and that the next
  `/assessment-fix` invocation resumes automatically.
- **Stopped at:** if halted — the finding ID or batch, the gate/step that
  failed, the failing output or corrected proposal, and the recommended next
  action.
- **Remaining:** open findings still in `.local/ASSESSMENT.md`.
- **Commit message:** confirm `.local/COMMIT-MSG.txt` was created or updated
  with an entry for each finding accepted this run (see **Commit message**
  below).
- Remind the operator: the working tree is **dirty and uncommitted** —
  review the `.local/ASSESSMENT.md` diff and the code diff, then commit when
  satisfied.

---

## Commit message

Immediately after each finding/batch is accepted (step 6 / B6) — not only at
the very end, so a mid-run stop still leaves an accurate partial draft —
upsert `.local/COMMIT-MSG.txt`, a plain-text git commit message body the
operator will use for the eventual commit. This is a file write, not a git
operation, so it is exempt from the "no git" rule.

- **If the file doesn't exist**, create it: a one-line conventional-commit
  subject summarizing the run so far (e.g. `docs: close N comprehensibility
  findings from assessment batch <range>`), a blank line, then one bullet
  per accepted finding. No `Co-Authored-By:` trailer — do not add one.
- **If it already exists** (uncommitted fixes from an earlier run this
  session), read it first. Leave its existing subject line and bullets
  untouched; append one new bullet per finding accepted in *this* run, same
  format, at the end of the file. Never duplicate a bullet for a finding ID
  already listed — check by ID before appending.
- **Bullet format:** `- <ID> (<file>): <one clause — what changed and why>.`
  Note inline, briefly, if the finding was auto-corrected (Low tier) or
  escalated from a doc gap to a real bug fix. Keep it minimal — one clause,
  not a restatement of the Problem/Fix text; the report and the code diff
  are the full record, this is a commit draft.
- Skip this step for a finding removed only because the staleness check (B2
  / step 2) found it already fixed — nothing changed in this run, so there's
  nothing to add to the message.
