---
description: Transform a plan into a machine-maintained .local/REFACTOR.<kebab>.md tracking file and register it in the .local/REFACTOR.md index (asks clarifying questions first)
argument-hint: [plan-path]
model: opus
---

# /refactor-init

Transform a human-authored plan into `.local/REFACTOR.<kebab-title>.md` — the
per-refactor tracking file that `/refactor-next`, `/refactor-checkpoint`, and
`/refactor-status` operate against — and register a row for it in the
`.local/REFACTOR.md` **index**.

The plan source is the argument if one is given, otherwise `.local/PLAN.md`.

`.local/REFACTOR.md` is a table of every refactor in the repo, exactly like
`.local/TODO.md` is for todo items. Each refactor's phases live in its own
`.local/REFACTOR.<kebab-title>.md`; a passing final-phase `/refactor-checkpoint`
removes the index row and moves the file to
`.local/completed/REFACTOR.<kebab-title>.completed.md`.

This command runs on **Opus**. It is the last point where design judgment is applied.
Before writing anything, Opus reviews the plan for risks, gaps, and ambiguities, asks
clarifying questions, and incorporates the answers. Downstream agents get no such
opportunity — what is unclear here will be invented there.

---

## Step 1 — Parse the plan

Read the plan file — the command argument if one was given, otherwise
`.local/PLAN.md`. If neither exists, report which path was tried and stop.

Extract:

- **Title** — from the `# Plan: [Title]` heading.
- **Kebab title** — the title lowercased, non-alphanumerics collapsed to single
  `-`, leading/trailing `-` stripped (e.g. `Cardsphere Wants Reconciliation` →
  `cardsphere-wants-reconciliation`; trim to the distinctive part if it runs
  long — `cardsphere-wants`). This names the tracking file and the index row.
  If `.local/REFACTOR.<kebab-title>.md` already exists, stop and report it —
  either the refactor is already initialized, or the kebab collides and needs a
  more specific title.
- **Context / Intent** — the opening context section.
- **Dependency diagram** — the `## Dependency order` (or equivalent) section.
  Parse it into a table: phase number → list of phase numbers it depends on.
- **Each phase** — for every `## Phase N —` section, capture:
  - Phase number and title.
  - "Modify:" or "Files:" list (the files the phase touches).
  - Every `### Na.` sub-step: its heading and full body content verbatim.
  - The "Phase N is complete when:" or `### Definition of Done` checklist items.
- **Assumptions** — any explicit assumptions or constraints section.
- **Test command** — infer from the plan (e.g., `go test ./...`, `npm test`). If the
  plan lists multiple verify commands, note the most comprehensive one.

---

## Step 2 — Assign models

For each phase, assign a model using these rules in priority order:

1. **Haiku** — phase title contains "checkpoint" or "test checkpoint", or the phase
   does nothing except run tests.
2. **Codex** — ALL of the following are true:
   - Every step has complete, literal code provided (no open design decisions left to
     the implementor).
   - The phase is purely mechanical: struct field additions, fixture file updates,
     route registration, import updates, boilerplate.
   - No step requires reading existing code to make a judgment call.
3. **Opus** — the phase defines a central contract, data model, or interface that
   multiple later phases implement against, AND getting it wrong cascades into rework
   across those dependents. Use Opus sparingly — one or two phases at most.
4. **Sonnet** — everything else: implementation with any judgment, tests that require
   structural decisions, React component architecture, any analysis.

Record the reasoning for each assignment. You will present it for review in Step 3.

---

## Step 3 — Sanity check and questions

Before writing any file, perform this review. For each issue found, formulate a
question or flag. Then ask all questions at once using `AskUserQuestion` (up to 4 per
call; batch multiple calls if needed).

### Issues to check

**Model assignments** — For each phase assigned Codex: confirm the spec is truly
complete. Is there any step where an agent must read existing code to decide what to
write? If yes, that phase should be Sonnet. Present your Codex assignments and ask
for confirmation.

**Spec completeness** — For each phase, ask: could an agent work through every step
using only the content in the plan, without opening files not listed in "Files to
modify"? Flag any step that implicitly requires knowledge of the existing code shape
(e.g., "add this field to the struct" without showing the struct, or "update the
handler" without specifying exactly what changes).

**Weak Definition of Done** — Any phase whose only DoD item is a compile check
(`go build` passes) rather than a test run is a risk. Flag it. Ask whether a test run
should be required instead.

**Dependency correctness** — Verify the dependency diagram against the phase contents.
Could any phase listed as independent actually conflict with another running in the same
sequence? Flag suspected ordering issues.

**Test command** — If the plan mixes Go and JS (or any two test ecosystems), confirm
the full test command. Present your inference and ask if it is correct.

**API contract changes** — Any phase that adds, removes, or renames a public API field,
route, or response shape should require an ADR. Flag these phases and ask whether an ADR
is required.

**Parallel safety** — The plan may note phases that are "independent of each other and
can run in parallel." Since `/refactor-next` runs one phase at a time sequentially, this
is informational only — but flag if any stated-parallel phases share a file, because
sequential edits to the same file from different phases can conflict.

**General agent clarity** — Read each phase as if you are an agent with no prior context.
Is anything ambiguous enough that a reasonable agent might make the wrong implementation
choice? Flag it. These are the issues most likely to produce plausible-but-wrong output.

### After questions are answered

Incorporate all answers. Update model assignments and any plan notes accordingly.
Proceed to Step 4 (write the tracking file), then Step 4b (register it in the index).

---

## Step 4 — Write `.local/REFACTOR.<kebab-title>.md`

Before writing, ensure `.local/` exists and `.local/.gitignore` exists containing exactly:

```text
*
!.gitignore
```

Write the per-refactor file to `.local/REFACTOR.<kebab-title>.md` using the schema
below (the schema writes `.local/REFACTOR.<TITLE>.md` as a placeholder —
substitute the real kebab title everywhere it appears). Every section is required.
Do not omit sections even if they have minimal content.

Each phase header carries `**Baseline:**` and `**Reviewed:**` fields, both written as `—`.
`/refactor-next` fills the first with the commit the phase starts from and the second with
the commit it had reviewed and adjudicated up to; `/refactor-checkpoint` diffs against the
first and reviews only what changed since the second. A phase that reaches the checkpoint
without a baseline can only be validated against its own self-report; one without a
reviewed marker gets a full review there instead of a cheap delta.

**Emit the HTML extraction markers exactly as shown in the schema** —
`<!-- shared:intent:start -->` / `:end`, the same for `hard-constraints` and
`definition-of-done`, and `<!-- phase:N:start -->` / `<!-- phase:N:end -->` around
every phase. `/refactor-next` and `/refactor-checkpoint` use them to `sed` out exactly
the region they need. Without them both commands must read the whole file — ~20k
tokens to retrieve one ~4k phase — and every later phase's steps land in a context
that should only hold the current one. Renumbering or reordering phases means moving
the markers with them.

**Do not add a `**Status:**` line to a phase header or a step section.** Phase state
belongs only in the `## Phase Map` row and step state only in the `### Step Index`
table. Duplicating it in prose creates a field nothing reads and agents forget to
update, which then reads as a real inconsistency to the next `/refactor-next`.

---

### Schema

```text
# Refactor: [Title]

<!-- Generated from [plan source] by /refactor-init on YYYY-MM-DD -->

<!-- shared:intent:start -->

## Intent

[2–4 paragraphs from the PLAN.md context section. What is being built, why, and what
the end state looks like. Written as a contract: agents that deviate from this intent
are out of scope.]

<!-- shared:intent:end -->


<!-- shared:hard-constraints:start -->

## Hard Constraints

[Explicit "must not change" rules derived from PLAN.md Assumptions and any flagged
API contract items. Add generic constraints that always apply:]

- Do not change any API route, field name, or response shape without an ADR.
- Do not leave `// TODO` markers without tracking them in the Session Log.
- Do not mark a phase complete if `[Test Command]` fails.
- Do not break existing passing tests.

<!-- shared:hard-constraints:end -->


## Model and Effort Guide

[Standard table plus plan-specific notes from Step 2 analysis:]

| Model  | Use for |
| --- | --- |
| Haiku  | Test-only phases, mechanical lookups |
| Sonnet | Implementation with any judgment, component architecture, test design |
| Opus   | Central contracts that cascade into multiple later phases |
| Codex  | Fully-specified mechanical phases: field additions, fixture updates, boilerplate |

[List any specific phases assigned Opus or Codex with the reasoning from Step 2.]

<!-- shared:definition-of-done:start -->

## Definition of Done

A phase is complete only when all of the following are true:

- Code is clean and consistent with `AGENTS.md` standards.
- No untracked `// TODO` or `// FIXME` markers introduced.
- All documentation that changed in behavior has been updated.
- New or updated tests cover the changed logic.
- `[Test Command]` passes.
- Every item in the phase's `### Definition of Done` checklist is satisfied.
- An ADR exists in `docs/decisions/` for any phase that changes a public contract
  (if flagged during /refactor-init review).

<!-- shared:definition-of-done:end -->


## Session Handoff Protocol

Every agent starts by reading:

1. `AGENTS.md`
2. `.local/REFACTOR.<TITLE>.md` §Intent, §Hard Constraints, §Definition of Done
3. The files listed in the current phase's **Files to modify** line

Never rely on conversation context surviving between sessions. If a phase's Step Index
still shows `Not started` or `In progress`, that phase is not complete.

## Orchestral Operation

Steps are run one phase at a time by invoking `/refactor-next` (with this
refactor's kebab title, or with no argument when it is the only one active). The
orchestrator reads `.local/REFACTOR.<TITLE>.md`, finds the next eligible phase,
and spawns a subagent at the assigned model tier. The subagent completes the
entire phase, updates this file, and returns a synopsis. The orchestrator relays
the synopsis and waits.

Run `/refactor-checkpoint` after every phase before advancing. `/refactor-status` shows
current state at any time. Both are read-only with respect to implementation.

One phase per `/refactor-next` invocation. The orchestrator does not chain phases.

## Test Command

[Exact command(s) to run. Examples:]

    go test ./...

[Or for mixed projects:]

    go test ./...
    npm test --prefix website

## Phase Map

| Phase | Title | Status | Depends on | Model |
| --- | --- | --- | --- | --- |
| 1 | [title] | Not started | — | Sonnet |
| 2 | [title] | Not started | 1 | Sonnet |
[... one row per phase ...]

## Session Log

<!-- Status is one of: Complete, Partial, Checkpoint failed, Review.
     /refactor-checkpoint validates the most recent Complete or Partial row and skips
     the rest, so bookkeeping rows must not use those two words. -->

| Date | Phase | Model | Status | Notes |
| --- | --- | --- | --- | --- |

---

<!-- phase:1:start -->

## Phase 1 — [Title]

<!-- No **Status:** field here. Phase state lives in ONE place, the ## Phase Map row,
     and step state in ONE place, the ### Step Index table. A prose Status header
     duplicating either is write-only: no command reads it, and phase agents update
     the table while leaving the prose stale, which then trips /refactor-next's
     consistency check on the NEXT invocation. -->

**Depends on:** —
**Model:** Sonnet
**Baseline:** —
**Reviewed:** —
**Files to modify:** `path/to/file.go`, `path/to/other.go`

### Standard Preamble

<!-- The three shared sections below are RE-STATED IN FULL by /refactor-next when it
     builds the subagent prompt. Write this preamble so the agent never needs to open
     .local/REFACTOR.<TITLE>.md itself: pointing at a section of a 90KB tracking file costs a
     subagent ~20k tokens to retrieve ~1k of content, and it drags the whole file --
     every other phase's steps included -- into a context that should hold only this
     phase. Name external reading here ONLY for real source files. -->

Read the following before starting:

1. `AGENTS.md` — code standards and conventions.
2. The §Intent, §Hard Constraints and §Definition of Done sections reproduced
   below — they are complete as given. **Do not open `.local/REFACTOR.<TITLE>.md`.**
3. Files you will modify: [repeat the Files to modify list as readable prose].

[Any phase-specific context an agent needs before reading the steps. Flag known
gotchas, constraints from prior phases, or invariants to preserve. If none, write:
"No additional context — proceed directly to the steps."]

[If the phase depends on reference material in another `.local/` document (tripwires,
design notes), quote the relevant passages here rather than citing section numbers.
The same retrieval cost applies: a citation makes the agent open and page a large
file; a quotation costs only the passage.]

### Step Index

| Step | Description | Status |
| --- | --- | --- |
| 1.a | [description] | Not started |
| 1.b | [description] | Not started |

### Step 1.a — [Name from PLAN.md]

[Verbatim content from PLAN.md, including all code blocks, logic descriptions,
and helper notes. Do not paraphrase or summarize — copy exactly.]

### Step 1.b — [Name]

[Verbatim content.]

### Definition of Done

[Checklist items from PLAN.md's "Phase N is complete when:" section, formatted as
a markdown checklist. Add any items surfaced during Step 3 review.]

- [ ] [criterion]
- [ ] [criterion]


<!-- phase:1:end -->

---

<!-- phase:2:start -->

## Phase 2 — [Title]

[Repeat the above structure for every phase.]
```

---

## Step 4b — Register the refactor in `.local/REFACTOR.md` (the index)

`.local/REFACTOR.md` is the index of every refactor in the repo — the same role
`.local/TODO.md` plays for todo items. It is **not** a per-refactor file.

If `.local/REFACTOR.md` does not exist, create it:

```markdown
# Refactors

| Refactor | Status | Phases | Summary |
| --- | --- | --- | --- |
```

If it exists but contains `## Phase Map` or `## Intent` (the old single-file
format, before this index existed), stop and tell the user to rename that file to
`.local/REFACTOR.<its-kebab-title>.md` and re-run — do not overwrite it.

Append one row for this refactor:

```text
| <kebab-title> | planning | 0 / <M> | <one line from §Intent> |
```

- **Status** is `planning` until the first phase starts (`/refactor-next` bumps
  it to `active`), `blocked` after a failed checkpoint, and the row is **removed**
  entirely when the final phase passes its checkpoint.
- **Phases** is `<completed> / <total>`; `<M>` is the phase count.

---

## Step 5 — Final output

After writing `.local/REFACTOR.<kebab-title>.md` and the index row, report to the user:

1. The kebab title, and confirmation the index row was added.
2. A summary table of all phases and their assigned models.
3. Any issues found during the sanity check and how they were resolved (or flagged
   as follow-up items in Hard Constraints).
4. Any open questions that could not be resolved and were noted in the file.
5. The command to begin: `Run /refactor-status to confirm, then /refactor-next to start.`
   (No argument needed while this is the only active refactor.)
