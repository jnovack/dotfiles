# /review-fix

Fix findings recorded in `.local/REVIEW.md` — one finding at a time, each fully
validated, regression-guarded, tested, and documented before it is accepted and
removed from the report. Each fix is performed by a dedicated subagent launched
at the model/effort the finding calls for; the orchestrator (you) independently
re-validates the subagent's work before accepting it.

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
- **Graph first.** Fix subagents must use the `code-review-graph` MCP tools
  (`semantic_search_nodes`, `query_graph`, `get_impact_radius`,
  `get_affected_flows`) before Grep/Read, per `CLAUDE.md`.
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
| Codex | `opus` | Codex is not launchable via the Agent tool (different vendor); substitute `opus` as the closest locally available reasoning-oriented model and note the substitution in the final report. |
| *(line absent)* | `sonnet` | Default when a finding predates this field. Note in the final report that a default was applied. |

**Effort → prompt instruction** (the Agent tool has no effort parameter; effort
is conveyed as explicit prose in the subagent's prompt):

| Effort | Instruction embedded in the subagent prompt |
| --- | --- |
| Low | "Apply the described fix directly once you've confirmed it's correct. Keep the regression-guard graph check brief — the directly impacted symbol is enough." |
| Medium | "Verify assumptions with the graph tools before applying the fix; re-derive it if gaps appear. Check at least one layer of callers/dependents via `get_impact_radius`." |
| High | "Thoroughly investigate the impact radius and affected flows before applying anything. Reason carefully through concurrency/design implications and edge cases, and make sure the regression test actually exercises them." |

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
  branching/no committing, graph-first tool usage, the pre-release repo
  conventions, and the **fix-accuracy tier rule** (verbatim, including the Low
  auto-correct/non-trivial-exception and the Medium+ stop-without-applying
  behavior).
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
  5. Sync documentation: GoDoc for any changed contract, external markdown
     (`README.md`, `AGENTS.md`, relevant ADRs, `docs/openapi.yaml`) if behavior
     or an API contract changed, and `.env.example`/`README.md` together for any
     flag/env change. Keep markdown lint-clean per `CLAUDE.md`.
  6. Run the **verify gate** itself before reporting back: `go build ./...`,
     `go vet ./...`, the scoped `golangci-lint run --new-from-rev=...` command,
     `make test`, and confirm the new/updated test is included and passing.
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

1. Re-run, yourself, the specific new/updated test(s) it named.
2. Re-run `make test` in full.
3. If the touched files could plausibly affect build/vet/lint scope beyond the
   named test (i.e. almost always), also re-run `go build ./...`, `go vet
   ./...`, and the scoped lint gate:
   `go run github.com/golangci/golangci-lint/cmd/golangci-lint@latest run --new-from-rev=$(git merge-base HEAD main)`.

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

- **Fixed:** for each accepted finding — ID, model/effort used (and any
  Codex→Opus or missing-field→Sonnet/Medium substitution applied), files
  touched, test added, docs updated.
- **Auto-corrected (Low):** any Low finding where the fix subagent applied a
  fix that differed from the report — note the report's proposal vs. what was
  applied and why.
- **Skipped (already fixed):** any findings step 2 found already resolved.
- **Stopped at:** if halted — the finding ID, the gate/step that failed (fix
  subagent's verify gate, orchestrator's independent re-validation, oversized
  impact, or a Medium+ proposed-fix rejection), the failing output or the
  corrected proposal, and the recommended next action.
- **Remaining:** open findings still in `.local/REVIEW.md`.
- Remind the operator: the working tree is **dirty and uncommitted** — review the
  `.local/REVIEW.md` diff and the code diff, then commit when satisfied.
