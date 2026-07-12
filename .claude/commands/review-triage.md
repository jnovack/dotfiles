---
description: Group open report findings into risk-ordered batches for a -fix command; backfills missing Model/Effort lines
argument-hint: [report-path]
model: sonnet
---

# /review-triage

Group and order the open findings in a report into batches a `-fix` command
can execute efficiently, and write the result to a companion `.TRIAGE.md`
file. This command changes no source code — it is a planning pass between
generation (`/review`, `/review-comprehensive`, `/assessment`) and execution
(`/review-fix`, `/assessment-fix`).

Arguments: `$ARGUMENTS` — path to the report file. Defaults to
`.local/REVIEW.md` if it exists, else `.local/ASSESSMENT.md`. If neither
exists (and no path was given), report that and stop.

---

## Why triage is a separate step

`-fix` commands process findings one at a time by default — the right model
when every finding needs its own independent regression test and
verification. It is the wrong model for a report containing many
low-ambiguity, single-file findings that share a fix shape: re-verifying
each one independently wastes the cheap ones' cheapness. Triage groups those
into batches so a `-fix` command can run one verification pass per batch
instead of one per finding, while still handling judgment-heavy findings
individually, with a checkpoint, exactly as before.

---

## Step 1 — Ensure every finding has a Model/Effort assignment

`-fix` commands require a `**Suggested Model/Effort:**` line on every finding
they process; this step guarantees one exists before any grouping happens.

For each finding in the report:

- If a `**Suggested Model/Effort:** <Model> / <Effort> — <reasoning>` line is
  already present in its block (added at generation time), trust it. You may
  *upgrade* effort — never downgrade — if grouping reveals a shared risk the
  isolated generation-time pass couldn't see (e.g. two findings in different
  files both rely on the same undocumented invariant: that's now a
  cross-file consistency risk, not two independent Low findings). You may
  also re-route a generation-time Haiku assignment to Codex under the
  Codex-first policy below (common in reports that predate the policy) — a
  model swap toward the cheaper executor is not a downgrade; effort itself
  never goes down. Update the line in the source report when you do either.
- If the line is absent (the report predates this field, or was written by a
  tool that doesn't emit it), assign one now using the sizing table below,
  then **write it back into the source report**, inserted immediately before
  that finding's `**Fix:**` line. Do not proceed to Step 2 for a finding
  until it has an assignment recorded in the source report itself — triage's
  own output file never duplicates finding content, so this is the only
  place the value persists.
  - **`**Fix:**` is not always a standalone line.** Some findings (typically
    ones whose fix is an instruction rather than a code replacement, e.g.
    "delete function X" or "correct `.env.example` to:") put prose directly
    after the marker on the same line: `**Fix:** Delete the local
    redeclaration at line 229...`. Match on the line *starting with*
    `**Fix:**`, not on exact equality to `**Fix:**` — an exact-match insert
    will silently skip every finding that uses the inline form. After
    inserting, count how many findings actually received the line and
    compare it against the total finding count from the index table; a
    mismatch means some form of `**Fix:**` wasn't matched.

### Sizing table

| Tier | Criteria |
| --- | --- |
| Codex / Medium | Zero ambiguity in fix correctness, zero behavior change, mechanical to apply — whether that's one location or repeated across many files. **Default tier for anything this cheap**, single-finding batches included: Codex execution costs no Claude tokens, and the orchestrator's mandatory independent post-batch validation applies exactly the same regardless of which model produced the diff, so routing zero-ambiguity work to Codex loses no rigor. |
| Haiku / Low | Same zero-ambiguity, mechanical shape as Codex/Medium above, but used only when a Codex handoff genuinely isn't viable for that finding (e.g. the fix needs a tool/capability Codex doesn't have in this environment). Do not choose Haiku/Low just because a batch is small, standalone, or "not worth the handoff" — per the operator's standing preference, cost minimization means Codex is the default whenever it can do the job, not a convenience call. |
| Sonnet / Low | No behavior change, but needs cross-file consistency or correctness on a widely-used interface/type/contract. |
| Sonnet / Medium | Small structural cleanup (dedupe, hoist, delete dead code, extract a helper) contained to one package; needs a caller check and/or a test touch-up. |
| Sonnet / High | The correct fix is a real behavior change, not just wording — needs verification of an assumption and a test before landing. |
| Opus / Medium | Needs Opus-level reasoning to get right (e.g. an actual concurrency-safety argument, not a restated assumption) but does **not** need a human product decision — the agent can resolve it correctly on its own once it reasons carefully, it just can't be trusted to a lighter model. |
| Opus / High | Architecture/ADR-governance conflict, or a product decision the report cannot make unilaterally. Requires a human checkpoint before any code is written. |

This table is illustrative, not exhaustive — any `<Model> / <Effort>` pair is
valid as long as the reasoning justifies it. When a finding doesn't fit a row
cleanly, pick the model by "how much reasoning does getting this right
require" and the effort by "how much verification does trusting it require,"
independently of each other, rather than forcing it into the nearest listed
combination.

Sizing follows blast radius and ambiguity, not the finding's severity label.
A Critical finding that is a one-line, unambiguous fix in one file is still
Codex/Medium (or Haiku/Low if Codex can't take it). A Warning whose fix
requires amending a governing ADR is Opus/High regardless of how small the
diff looks.

**Codex-first policy.** Standing operator preference: minimize Claude token
spend by preferring Codex over any Claude model whenever the fix is
zero-ambiguity and mechanical, regardless of batch size — a lone orphaned
Low finding still goes to Codex rather than Haiku, since the fixed cost of
writing a handoff prompt is trivial next to even one Haiku subagent
dispatch, and the operator has already confirmed that Codex's stop-the-run
handoff friction is not a concern. Only fall back to Haiku/Low when Codex is
not a viable executor for that specific finding.

**Before assigning a doc-only tier**, check whether the fix asserts a
rationale for a magic number, formula, or derived value. If so, re-derive
the value from the code it describes rather than trusting the pattern of a
nearby, already-explained constant — two constants that look like siblings
can silently drift out of sync, and the "undocumented" value may be wrong,
not just unexplained. If it doesn't hold up, the finding is a real bug, not
a doc gap — re-size it (Sonnet/High or higher) and say so in the batch
rationale in Step 2.

## Step 2 — Group into batches

A batch is a set of findings a single execution pass can safely apply
together. Findings belong in the same batch only if **all** of:

- Same Model/Effort tier (tier boundaries are hard; never mix tiers in one batch).
- No finding in the batch depends on another (applying one doesn't change
  the code another's fix targets).
- Combined, they touch a number of files a single diff review can actually
  be checked against (soft cap: 10 files per batch — split larger groups).

Within a tier, prefer grouping findings that touch the *same file* into one
batch, so the executing agent/tool reads each file once instead of once per
finding.

Every Opus/High finding, and every finding whose reasoning says something
like "decide before writing," "needs a human decision," or "requires
amending an ADR," gets its **own batch of size 1**, marked
`Requires checkpoint: yes`. Never bundle a judgment call in with anything
else, even another Opus/High finding — each needs its own approval.

## Step 3 — Order the batches

1. Codex/Medium batches first — zero Claude-token cost to execute, cheapest
   and safest, shrinks the list fastest. This is the position Haiku/Low used
   to occupy before the Codex-first policy above; Haiku/Low batches (now
   rare) run immediately alongside these, same rationale.
2. Sonnet/Low, then Sonnet/Medium — grouped by package where possible, so
   cross-file consistency checks happen once per package instead of once
   per finding.
3. Sonnet/High — one batch at a time, each with its own verification.
4. Opus/Medium — needs careful Opus-level reasoning but no checkpoint;
   schedule after Sonnet/High since it's higher-trust-required, before
   Opus/High since it doesn't block on operator sign-off.
5. Opus/High — last, one at a time, each with a checkpoint before starting.

---

## Output

Write `.local/<REPORT-NAME>.TRIAGE.md` (e.g. `.local/REVIEW.TRIAGE.md` for a
`.local/REVIEW.md` source, `.local/ASSESSMENT.TRIAGE.md` for
`.local/ASSESSMENT.md`). Before writing, ensure `.local/` exists and
`.local/.gitignore` excludes it (create with `*` / `!.gitignore` if missing).

```markdown
# <Report Name> Triage

> Source: `.local/<REPORT-NAME>.md` (<N> findings, <M> batches)
> Generated: <datetime in localtime — run `date`, do not guess>
> <K> findings had their Suggested Model/Effort backfilled into the source
> report by this run.

## Execution order

1. Batch 01 — Codex / Medium
2. Batch 02 — Codex / Medium
   ...
<M>. Batch <NN> — Opus / High (checkpoint)

---

## Batch <NN> — <Model> / <Effort>

**Findings:** #ID-1, #ID-2, #ID-3
**Files:** path/to/a.go, path/to/b.go
**Rationale:** <one line: why these are grouped, what makes them safe to batch>
**Requires checkpoint:** yes | no

---
```

Batches appear in the file in the exact order they should be executed. This
file is consumed by `/review-fix` or `/assessment-fix`; it is an index only
— finding content, Problem/Issue text, and Fix blocks stay in the source
report as the single source of truth. Re-run `/review-triage` any time the
source report changes materially (new findings added, or enough findings
removed that batches should be recomputed); a `-fix` command noticing the
triage file's finding count no longer matches the source report's open
findings should report the mismatch and suggest re-running triage rather
than guessing.
