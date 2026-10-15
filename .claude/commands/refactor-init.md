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
   across those dependents. Use Opus sparingly — one or two phases at most. The
   cohesion phase added in Step 2c is always Opus and does not count toward that limit.
4. **Sonnet** — everything else: implementation with any judgment, tests that require
   structural decisions, React component architecture, any analysis.

Record the reasoning for each assignment. You will present it for review in Step 3.

---

## Step 2b — Build the design map and placement decisions

Every phase agent sees its own section and its own files, and nothing else. Without
a picture of the whole project, each one puts new code next to where it is used,
copies the nearest template, and adds one more entry to whatever hand-maintained list
it touches. Each choice is locally reasonable. Repeated across phases, they produce a
project of hundreds of near-duplicate functions with no coherent shape. This step is
the one point where placement is decided with the whole project in view, and the
§Design Map it produces is pasted into every phase prompt.

1. **Map the modules the refactor touches or should reuse.** Derive them from the
   conventions file's architecture rules, the ADR index, any architecture or discovery
   doc, and the code graph (`get_architecture_overview`, `list_communities`) where the
   repo has one. For each module: what it owns and which shared helpers it already
   provides. Keep it to the modules that matter here — the section is pasted into
   every phase prompt, so aim for under ~60 lines.
2. **List the single sources of truth** the refactor touches: lists, constants,
   mappings and contracts that should exist once. For each, name the authoritative
   copy and how the others derive from it. Where copies are already hand-maintained,
   name every copy and the test that keeps them aligned, if any.
3. **Decide placement for everything new or moved** — each function, type, constant,
   file and list entry the plan introduces. Search for an existing near-equivalent
   first (graph semantic search, then grep by behavior rather than by name). Record
   where it lives, what it reuses or extends, and why it is not shared if it is not.
4. **Apply the rule of three.** A step that says "mirror", "copy" or "same as X",
   that duplicates an existing block, or that adds the third or later hand-maintained
   copy of a list, constant or mapping, must carry a placement decision:
   - **Extract** — add the extraction as a step in the earliest phase that needs it,
     so later phases reuse it instead of copying; or
   - **Copy, with a reason** — recorded in the placement table, plus the parity
     test that keeps the copies aligned.

   "The original is unexported" or "lives in another package" is not a reason by
   itself: exporting it or moving it to a shared package is usually the smaller
   long-term change. If a Hard Constraint forbids touching the original, ask the user
   in Step 3 rather than defaulting to the copy. When the plan has phases mirror a
   template component, list what the copy shares with the template and what differs:
   shared mechanics go in an extracted helper, and only the differences are written
   per copy.

   Seen 2026-10-06 (moxfall `cardsphere-index`): the plan told a phase to copy the
   prices stage's User-Agent constant because it was unexported, and told every phase
   to "mirror otags". The stage list ended up hand-maintained in about a dozen places,
   and each phase added one more entry plus a test to keep the copies aligned. Nobody
   asked whether there should be one list.

Placement choices with real alternatives (extract vs copy when a constraint blocks
extraction, which shared package a helper belongs in) are questions for Step 3.

## Step 2c — Add the cohesion phase

Per-phase reviews see one phase's diff, so nothing in the pipeline reviews the
refactor as a whole. Add a **Cohesion pass** phase, on **Opus**, using the template
in the schema. Insert it immediately before the plan's final validation, ADR or
release phase if it has one; otherwise append it last. It depends on the phase before
it, and the phase after it now depends on it. Renumber phases, dependencies and
markers to match.

Skip it only for a refactor of one or two phases, and say so in Step 5.

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

**Placement** — Present the Step 2b decisions that need the user: every copy kept
because a constraint blocks extraction, and every helper whose home is a genuine
choice. Recommend the extraction first unless it breaks a Hard Constraint.

**General agent clarity** — Read each phase as if you are an agent with no prior context.
Is anything ambiguous enough that a reasonable agent might make the wrong implementation
choice? Flag it. These are the issues most likely to produce plausible-but-wrong output.

### After questions are answered

Incorporate all answers. Update model assignments, the design map and placement
decisions, and any plan notes accordingly. Proceed to Step 4 (write the tracking file), Step 4b (register it in the index),
then Step 4c (independent review against the repository).

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
`<!-- shared:intent:start -->` / `:end`, the same for `hard-constraints`,
`definition-of-done` and `design-map`, and `<!-- phase:N:start -->` / `<!-- phase:N:end -->` around
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


<!-- shared:design-map:start -->

## Design Map

[From Step 2b. Where code belongs in this project. Every phase agent receives this
section; it is how a phase sees past its own files. Keep it under ~60 lines.]

### Modules

| Module | Owns | Shared helpers it provides |
| --- | --- | --- |
| `[path]` | [responsibility] | [helpers phases should reuse] |

### Single sources of truth

- [List, constant, mapping or contract] — authoritative copy: `[path]`; others derive
  by [mechanism]. [Or: deliberately duplicated in `[paths]` because [reason]; kept
  aligned by `[test name]`.]

### Placement

| New or moved | Lives in | Reuses / extends | Why not shared (or: shared) |
| --- | --- | --- | --- |
| `[symbol or file]` | `[path]` | `[existing helper]` | [reason] |

[Phase agents append rows here for anything they add that this table did not
anticipate, and for any file they changed outside **Files to modify** for placement.]

### Follow-ups

[Consolidations found during the refactor that were too large for it. Filled in by
phases and by the cohesion pass. Start as "None."]

<!-- shared:design-map:end -->


## Session Handoff Protocol

Every agent starts by reading:

1. `AGENTS.md`
2. `.local/REFACTOR.<TITLE>.md` §Intent, §Hard Constraints, §Definition of Done,
   §Design Map
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
current state at any time and is read-only. `/refactor-checkpoint` fixes defects in the
phase it validates and repairs the next phase's plan, but never implements the next phase.

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
2. The §Intent, §Hard Constraints, §Definition of Done and §Design Map sections
   reproduced below — they are complete as given. **Do not open
   `.local/REFACTOR.<TITLE>.md`.**
3. Files you will modify: [repeat the Files to modify list as readable prose].

[If the phase adds code the §Design Map's Placement table covers, name those rows
here so the agent reuses what they point at.]

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

<!-- phase:2:end -->

---

<!-- phase:K:start -->

## Phase K — Cohesion pass

**Depends on:** K-1
**Model:** Opus
**Baseline:** —
**Reviewed:** —
**Files to modify:** any file this refactor changed (`git diff <Phase 1 Baseline>`
plus the refactor's untracked files), plus the shared destination of each
consolidation, recorded in §Design Map

### Standard Preamble

Read the following before starting:

1. `AGENTS.md` — code standards and conventions.
2. The §Intent, §Hard Constraints, §Definition of Done and §Design Map sections
   reproduced below — they are complete as given. **Do not open
   `.local/REFACTOR.<TITLE>.md`.**
3. The refactor's whole change set: `git diff <Phase 1 Baseline>` plus untracked
   files.

Every earlier phase saw only its own files. This phase reviews the refactor as a
whole, and its job is **subtraction**: parallel code paths, copied constants and
lists, helpers that should be shared, code in the wrong module, and indirection that
does not pay for itself. It is not a style pass and adds no features.

### Step Index

| Step | Description | Status |
| --- | --- | --- |
| K.a | Inventory against the Design Map | Not started |
| K.b | Find duplication and misplacement | Not started |
| K.c | Consolidate | Not started |
| K.d | Record | Not started |

### Step K.a — Inventory against the Design Map

From the whole-refactor diff, list every new or moved function, type, constant, file
and hand-maintained list entry. Compare each with the §Design Map Placement table and
note every difference between plan and code.

### Step K.b — Find duplication and misplacement

For each inventory item, search the whole repository for near-equivalents — code-graph
semantic search where available, then compare bodies, not names. Flag:

- a list, constant or block now hand-maintained in three or more places;
- template-mirrored code whose shared mechanics are repeated in each copy;
- a helper in a leaf package whose siblings live in a shared one;
- a wrapper or abstraction with one caller that adds nothing;
- a parity test that exists only to keep duplicated copies aligned.

### Step K.c — Consolidate

Apply each consolidation that preserves behavior and stays within the refactor's
footprint plus one shared destination. Keep the test command green after each one.
When a consolidation removes a hand-maintained copy, replace its parity test with a
test on the single source. Do not change a public API, wire, config or schema shape —
§Hard Constraints apply here as everywhere. Record a consolidation that is larger than
this, or that reaches code the refactor never touched, under §Design Map Follow-ups
instead of doing it.

### Step K.d — Record

Update the §Design Map Placement table and single-sources list to match the code, and
list every applied and declined consolidation in the Session Log row.

### Definition of Done

- [ ] Every K.a inventory item sits where §Design Map says, or the table now records
  why it does not.
- [ ] Each applied consolidation kept `[Test Command]` green; each declined one has a
  reason or a Follow-ups entry.
- [ ] No public contract changed.
- [ ] `[Test Command]` passes.

<!-- phase:K:end -->
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

## Step 4c — Independent review against the repository

Step 3 checks the plan against *itself*. That is not enough: the defects that
survive it are the ones only visible from the code — a DoD `git grep` that can
never come back empty because an out-of-scope file matches, a file list that
misses half the references a rename must touch, a new flag that breaks the
repo's env-var or build-file convention, a ported default that quietly drops a
safety guard the old code had. Every phase agent inherits these verbatim and
"fixes" them by inventing scope. Catch them here, while the only artifact is a
plan.

Spawn a **new `general-purpose` subagent on `model: opus`, in the foreground**.
Never review the file yourself in its place, and never reuse an agent that
helped write it: an author re-reads the intent it had while writing, so a step
that says the wrong thing still looks right to it. This is the same rule
`/refactor-next` applies to its post-phase review.

Give it the tracking file's path (it reads the whole file — cross-phase
consistency is part of the job), and these standing instructions:

- **Report only.** Never edit a file, never run a git write command, never
  touch a live service or a network endpoint.
- **Load context first:** the repo's `CLAUDE.md`/`AGENTS.md`, the user's
  project memory notes if the session has any, the ADR index and only the ADRs
  the plan touches, and the docs the plan changes. Standing user decisions in
  memory or `CLAUDE.md` outrank the plan; flag any step that contradicts one.
- **Verify, don't trust.** Check every claim the plan makes about current code
  against the code, citing `file:line`. Prefer the repo's code-graph tools, if
  it has them, for callers/consumers before grepping.
- **Run every mechanical DoD check now** (`git grep`, `make -n`, …) and judge
  whether it *can* pass at the end of its phase given that phase's file list and
  the plan's out-of-scope list. A check that cannot pass without breaking scope
  is Blocking.
- **Reference coverage.** For every symbol, flag, env var, script, output path
  or field the plan renames or removes, search the whole repo and confirm each
  hit is covered by some phase's file list or is explicitly left alone —
  including config examples, build files, help text, error strings, templates,
  docs and project instruction files.
- **Contract coverage.** For every output shape, path or flag that changes,
  confirm every reader is updated in the same phase, including non-code readers.
- **Repo conventions.** New surface (flags, env vars, build targets, log
  streams, output locations, naming) must match the patterns already in the
  repo. Name the pattern and where it is stated.
- **Behavior parity and safety.** For code being ported or moved, find the
  guards, defaults, fail-closed paths and ordering assumptions in the original,
  and flag any the plan drops or any default that changes a safety posture.
- **Test-first.** Each phase needs tests for its negative cases, parity tests
  where it replaces existing behavior (proven before the old code is deleted),
  and a named guard test for each deliberate divergence or decision; each DoD
  requires the test command.
- **Interoperability over individual functions.** Phase ordering, naming drift
  between phases, each phase leaving the tree buildable and green, and
  instructions that clash with standing rules (e.g. "commit the file" when the
  user forbids `git add`).
- **Unnecessary complication.** New packages, abstractions, exported surface
  or phases that do not pay for themselves.
- **Placement and cohesion.** Check the §Design Map against the code: does each
  Placement row point at the right module, and does an existing near-equivalent
  already do the job (search by behavior, not name)? Flag every "mirror", "copy"
  or third-copy step without a placement decision, every copy justified only by
  visibility ("unexported", "other package"), and every shared mechanic a
  template-mirroring phase would repeat. Confirm the cohesion phase is present and
  correctly placed.
- **Output:** Blocking / Should-fix / Nits, most severe first. Each finding
  names the phase, the problem, evidence (`file:line` or quoted plan text) and
  a proposed fix that has itself been checked against documented intent. Then
  what the plan gets right (to preserve), then open questions only the user can
  decide. An empty section is a useful result — do not pad.

Adjudicate the report yourself:

1. Spot-check each finding's evidence against the tree; dismiss what does not
   hold, with the reason.
2. Put every open question and every finding whose fix is a genuine user choice
   to the user at once via `AskUserQuestion` (up to 4 per call, recommended
   option first).
3. Apply every surviving fix and every answer to the tracking file. Record each
   user decision inline where it applies, dated, with its reason, so phase
   agents cannot "simplify" it away.
4. Append one Session Log row: `| <date> | — | Opus | Review | init review:
   <N> blocking, <N> should-fix applied, <N> dismissed; decisions: … |`.
   (`Review` is the status `/refactor-checkpoint` skips, so this row is never
   mistaken for a completed phase.)

**One review round.** Do not re-spawn a reviewer over your own fixes; each
phase's `/refactor-next` review and `/refactor-checkpoint` still stand behind
this one.

---

## Step 5 — Final output

After writing `.local/REFACTOR.<kebab-title>.md` and the index row, report to the user:

1. The kebab title, and confirmation the index row was added.
2. A summary table of all phases and their assigned models, including where the
   cohesion phase was placed (or why it was skipped).
3. The placement decisions from Step 2b: what will be extracted, what stays copied
   and why.
4. Any issues found during the sanity check and how they were resolved (or flagged
   as follow-up items in Hard Constraints).
5. The Step 4c review outcome: findings by severity, how many applied, how many
   dismissed and why, and the user decisions recorded.
6. Any open questions that could not be resolved and were noted in the file.
7. The command to begin: `Run /refactor-status to confirm, then /refactor-next to start.`
   (No argument needed while this is the only active refactor.)
