---
description: Multi-agent code review across 6 dimensions; batched, resumable, run any subset; consistency is a whole-repo pass; writes .local/REVIEW.md (~5x token cost of /review)
argument-hint: [path] [dimension...]
model: sonnet
---

# /review-comprehensive

Run a multi-agent code review and produce `.local/REVIEW.md`. You are the
orchestrator: follow the steps below in order, dispatching one subagent per
(dimension, batch) unit via the `Agent` tool. You never read source files or
findings yourself — subagents write findings to disk and return only counts,
so your context stays flat regardless of repo size.

Arguments are optional and order-independent:

- A **path** (e.g. `src/`) scopes all file discovery to that path. Default: full repo.
- One or more **dimension names** run only those dimensions. Default: all six.
  Dimensions: `null-errors`, `resources`, `concurrency`, `security`, `tests`,
  `consistency`. (`all` is also accepted, meaning every dimension.)

Examples:

- `/review-comprehensive` — all dimensions, whole repo
- `/review-comprehensive security` — security only, whole repo
- `/review-comprehensive src/ security concurrency` — two dimensions, scoped to `src/`
- `/review-comprehensive consistency` — the whole-repo convention pass on its own

Five dimensions (`null-errors`, `resources`, `concurrency`, `security`,
`tests`) are **batched**: each reviews one batch of files at a time.
`consistency` is a **whole-repo pass** — one agent reads the entire file set,
because convention deviations are only visible against patterns the whole
codebase has established. Token cost is roughly 5× a standard `/review` when
all dimensions run; run a subset to spend less.

**Batched, resumable, and cumulative.** Every (dimension, batch) result is
written to `.local/.review-comprehensive/` the moment it completes, and
`ledger.json` records exactly what is finished. Consequences:

- **Resume:** if a run is cut short, re-run the same command — it reads the
  ledger, skips finished (dimension, batch) pairs, and continues.
- **Run in pieces:** run `security` today and `concurrency` tomorrow; each run
  adds findings to the same on-disk set.
- **Cumulative report:** every run regenerates `.local/REVIEW.md` from all
  findings gathered so far, with a **Coverage** section so a partial report is
  never mistaken for a comprehensive one.

Re-running with a **different path** starts fresh (the prior file set no
longer applies); the **same path** accumulates.

---

## Step 1 — Plan (resume or discover)

Workdir: `.local/.review-comprehensive/`. Before anything else, ensure
`.local/` exists and `.local/.gitignore` exists containing exactly `*` and
`!.gitignore` on two lines.

Parse the arguments: tokens matching a dimension name (or `all`) select
dimensions; the first remaining token is the scope path (default `.`).

Read `.local/.review-comprehensive/ledger.json` if it exists. Its shape:

```json
{
  "scope": ".",
  "summary": "one sentence on languages and structure",
  "batches": [{ "id": "001", "label": "internal/auth", "files": ["..."] }],
  "completed": { "security": ["001", "002"], "consistency": ["ALL"] }
}
```

- **Resume** if the ledger exists, its `scope` equals this run's scope, and
  `batches` is non-empty: reuse `summary`, `batches`, and `completed` as-is.
- **Fresh start** otherwise: dispatch a discovery subagent (below), build the
  batches yourself from its file list, delete any stale `batch-*.json` files
  in the workdir, set `completed` to `{}`, and write the initial ledger.

**Discovery subagent** (one `Agent` call, `subagent_type: "general-purpose"`):
ask it to list every source file under the scope path — excluding build
artifacts, vendored/third-party code, generated files (`*.pb.go`, `*.gen.*`,
`dist/`, `vendor/`), lockfiles, and binaries — plus one sentence describing
the languages and top-level structure. Have it return the file list and
sentence; if the list is empty, report that and stop.

**Batching — package-coherent, soft cap 20 files.** Batches must group *like*
files so a reviewer compares apples to apples, not arbitrary slices:

1. Group the file list by directory.
2. Walk directories in path order. Pack whole directories into the current
   batch while the total stays ≤ 20 files; a directory is never split across
   batches merely to fill a batch.
3. If a single directory alone exceeds 20 files, it becomes its own
   consecutive batches (only that directory's files, split at 20).
4. Prefer merging small sibling directories (same parent) into one batch over
   mixing unrelated trees; start a new batch at a top-level boundary even if
   the current one is under the cap.
5. Give each batch a zero-padded `id` (`001`, `002`, …) and a `label` naming
   its directory or directories.

Write the ledger, then report the plan: N batches, their labels, and which
dimensions this run will execute.

After every unit of work below, rewrite `ledger.json` with the updated
`completed` map — the ledger on disk must always reflect reality, so an
interruption at any point resumes cleanly.

---

## Step 2 — Analyze

For each batch in order: determine which selected batched dimensions have not
yet completed that batch (per `completed`). Skip the batch if none. Otherwise
launch the pending dimensions as **parallel `Agent` calls in a single
message** (`subagent_type: "general-purpose"`, one call per dimension), and
wait for all of them to finish before updating the ledger and moving to the
next batch.

Each analysis subagent's prompt is assembled from three parts, in order:

1. The dimension's prompt from **Dimension prompts** below (which embeds the
   **Base rules**).
2. The file list: `Files to read (THIS BATCH ONLY — do not read anything
   else):` followed by the batch's files, one per line.
3. The **write instruction**:

   > Write your findings as a JSON array to the file
   > `.local/.review-comprehensive/batch-<id>-<dimension>.json`. Each element
   > must be an object with exactly the fields in the finding contract below.
   > If you find nothing, write an empty array: `[]`. Overwrite the file if it
   > already exists. Return only the number of findings you wrote.

   …followed by the **Finding contract** below.

After the batched dimensions, if `consistency` is selected and not yet
complete: launch one agent with the consistency prompt, the ENTIRE file set
(all batches' files), and the same write instruction targeting
`batch-ALL-consistency.json`. Record it in `completed` as `["ALL"]`.

If any subagent fails or returns without writing its file, leave that
(dimension, batch) out of `completed`, note it, and continue — the next run
retries it.

---

## Step 3 — Synthesize

Runs every time, even after a partial analyze. Compute a coverage line for
all six dimensions: `complete` (every batch done, or `ALL` for consistency),
`PARTIAL` (some batches done), or `not run`.

Dispatch one synthesis subagent (`subagent_type: "general-purpose"`) with this
prompt content:

- All findings are stored as JSON files named `batch-<id>-<dimension>.json`
  in `.local/.review-comprehensive/`; read every `batch-*.json` file and
  combine their findings into one list.
- The repository summary, the scope path, and the coverage line you computed.
- Instructions:
  1. Deduplicate: same file+lines reported by multiple dimensions — keep the
     most specific description; if their `model_effort` values differ, keep
     the higher-effort one.
  2. Assign severity consistently: Critical (crash/data-loss/exploitable),
     High (likely bug or significant security weakness), Medium (will cause
     problems at scale), Low (minor refinement).
  3. Assign IDs `#MODULE-TYPE-NN`: MODULE = 2–5 char uppercase file
     abbreviation; TYPE = 2–5 char issue class (`NULL` `INJ` `RACE` `LEAK`
     `SEC` `ERR` …); NN = 2-digit 1-based counter incrementing globally
     across the report (never reset per module-type pair) so every full ID
     is unique.
  4. Write the complete `.local/REVIEW.md`:
     - `# Code Review` header with generated datetime (run `date` — do not
       guess), reviewer, scope.
     - `## Coverage` — the scope and the coverage line; if any dimension is
       PARTIAL or not run, say plainly this is not a comprehensive review.
     - `## Summary` — 3–5 sentences: dominant patterns, top concerns.
     - `## Finding Index` — table: ID | Severity emoji+label | File | Title.
     - `## Findings by File` — per-file blocks ordered by highest severity in
       that file; each finding: severity-emoji heading with ID, Line(s),
       Issue, Scope (only when the finding's `scope` field is non-empty),
       Suggested Model/Effort (copy `model_effort` verbatim), Fix as a
       complete runnable fenced code block with language tag, Rationale, Test.
     - `## Severity Reference` — the 4-level table with emoji labels
       (🔴 Critical, 🟠 High, 🟡 Medium, 🔵 Low).
     - `## Quick Wins` — 3–5 highest-leverage changes.
     - If no findings: say so and note where static analysis has limited
       coverage.

Then report to the user: findings gathered per dimension, the coverage state,
and where the report was written.

---

## Finding contract

Every analysis subagent writes arrays of objects with exactly these fields:

```text
file:         string — path
lines:        string — e.g. "42" or "42-51"
severity:     one of: critical | high | medium | low
title:        string — short
issue:        string — what is wrong and why it matters
scope:        string — empty unless the minimal fix violates an ADR/contract;
              then one or two sentences on which and why the reported fix is larger
fix:          string — complete runnable replacement code
fix_language: string — language tag for the fix block
rationale:    string — why this fix
test:         string — how to verify
model_effort: string — "<Model> / <Effort> — <one sentence>"
```

## Base rules (embed in every dimension prompt)

> Only report findings supported by concrete code evidence representing a real
> bug, security risk, reliability issue, or meaningful maintainability
> problem. Do not speculate. Do not flag risks already handled elsewhere in
> the codebase. Verify exact line numbers before reporting.
>
> Before writing a fix, check it against governing intent: the nearest ADR
> (docs/decisions/ or equivalent) and the touched function/type's doc comment.
> A minimal fix that contradicts either is not minimal — it is wrong. If the
> smallest patch conflicts with documented intent, propose the
> architecturally-correct fix instead (even if larger) and set the `scope`
> field explaining why. Leave `scope` empty when the minimal and correct fix
> are the same.
>
> For every finding, set `model_effort` to the model and effort a fix agent
> would need to correctly apply and verify the fix, formatted as
> "<Model> / <Effort> — <one sentence: blast radius or ambiguity>" using
> Model in {Haiku, Sonnet, Opus, Codex} and Effort in {Low, Medium, High}.
> Size by blast radius and ambiguity, not by severity. Codex-first: any
> zero-ambiguity, mechanical fix defaults to Codex/Medium — a Critical
> finding with an unambiguous one-line fix in a single file is still
> Codex/Medium; use Haiku/Low only when a Codex handoff is not viable for
> that finding. A Medium finding whose correct fix needs a real
> concurrency-safety argument is Opus/Medium if the agent can resolve it
> correctly on its own; a finding whose fix contradicts a governing ADR or
> requires a product decision the report cannot make unilaterally is
> Opus/High regardless of diff size. Pick Model by how much reasoning
> correctness requires and Effort by how much verification trusting it
> requires, independently of each other.
>
> Repository: [the one-sentence summary from discovery]

<!-- Keep these dimension prompts in sync with the per-file checklist in
review.md and the summary in ../docs/README.review-commands.md -->

## Dimension prompts

**null-errors** — "You are reviewing for ABSENT-VALUE SAFETY and ERROR
PROPAGATION only. [Base rules] Check: 1. Every value that could be null, nil,
None, undefined, empty, zero-value-invalid, or a typed null — is it checked
before use? 2. Every operation that can fail — is the error/exception checked?
Does propagation preserve cause/context? Is nothing silently swallowed or
replaced with a misleading message? Ignore all other issue types."

**resources** — "You are reviewing for RESOURCE LIFECYCLE only. [Base rules]
Check: every file handle, connection, lock, socket, goroutine, thread, timer,
ticker, request body, response body, or allocated resource — is there a
guaranteed release on all exit paths including error paths? Ignore all other
issue types."

**concurrency** — "You are reviewing for CONCURRENCY only. [Base rules]
Check: every value accessed from multiple goroutines/threads/tasks — is it
synchronized or immutable? Every async operation — is its lifetime bounded,
cancellable where appropriate, and failure observable? Ignore all other issue
types."

**security** — "You are reviewing for SECURITY only. [Base rules] Check all
three areas: 1. Trust boundary validation — every value from user input, env
vars, config, external APIs, CLI args, HTTP headers, serialized data, or
filesystem state — validated or sanitized before use? 2. Credential/secret
exposure — can any variable, field, error message, panic, response, metric,
trace, or log line leak a secret, key, token, credential, or PII?
3. Injection surfaces — every place external data is composed into a query,
shell command, template, URL, HTTP header, regex, file path, archive path, or
code expression — escaped, parameterized, allowlisted, or otherwise safe?
Ignore all other issue types."

**tests** — "You are reviewing for BASIC TEST COMPLETENESS only. [Base rules]
Check: for each tested function or behavior — are negative cases present?
Boundary conditions? Error paths? Do tests rely on timing assumptions, global
state mutation, ordering, network access, local machine state, or
implementation details? Also flag any exported or public function with zero
test coverage. Note: you are NOT performing a comprehensive test audit — that
is /review-tests. Only flag clear, obvious deficiencies. Ignore all other
issue types."

**consistency** (whole-repo) — "You are reviewing for CONVENTION CONSISTENCY
only. [Base rules] Identify the naming, error-handling, logging, testing, and
structural patterns already established in this codebase, then flag
deviations. Do not flag stylistic preferences — only deviations from patterns
the codebase has already committed to. Ignore all other issue types."
