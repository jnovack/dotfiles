---
description: Execute the next eligible phase of a refactor via a subagent at the phase's assigned model
argument-hint: [<refactor>]
---

# /refactor-next

Run the next incomplete phase in a refactor plan. One phase per invocation — do not chain.

---

## Step 0 — Select the refactor

Every refactor has a tracking file `.local/REFACTOR.<kebab>.md`; `.local/REFACTOR.md`
is the **index** listing them all.

- **Argument given** — treat it as the kebab title. If `.local/REFACTOR.<arg>.md`
  does not exist, report that and stop.
- **No argument** — read the `.local/REFACTOR.md` index table. Take the single row
  whose Status is `planning` or `active`. If there are none, report "no refactor
  in progress — run `/refactor-init`" and stop. If there is more than one, list
  them and ask which (require the argument).
- **Back-compat** — if `.local/REFACTOR.md` itself contains `## Phase Map` or
  `## Intent`, it is the old single-file format. Stop and tell the user to rename
  it to `.local/REFACTOR.<kebab>.md` and create the index (an easy
  `/refactor-init` re-run, or a manual two-line index file).

The result is the **tracking file**. Everywhere below, `REFACTOR.<kebab>.md` means
that file — never the index.

---

## What to do

1. Read only what you need from `.local/REFACTOR.<kebab>.md`, not the whole file. It grows to
   ~90KB and a full read costs ~20k tokens to retrieve the ~4k you actually use. Pull
   `## Phase Map` and `## Session Log` with `grep`/`sed`, then extract regions by their
   markers:

   ```bash
   sed -n '/phase:N:start/,/phase:N:end/p' .local/REFACTOR.<kebab>.md
   sed -n '/shared:intent:start/,/shared:intent:end/p' .local/REFACTOR.<kebab>.md
   ```

   Match on the bare marker text, not the full `<!-- … -->`, and brace any variable:
   in zsh `$name:start` parses `:s` as a parameter modifier and silently matches
   nothing, and a `!` inside double quotes triggers history expansion. So
   `"/shared:${name}:start/,/shared:${name}:end/p"`, never `"/shared:$name:start/…"`.
   A silent empty extraction is the failure mode — check the output is non-empty.

   If a file predates the markers (no `<!-- phase:1:start -->` anywhere), fall back to
   reading by line range and add the markers as you go.
2. In `## Phase Map`, find the first row where:
   - Status ≠ `Complete`, **and**
   - Every phase listed in "Depends on" has Status = `Complete` (or the field is `—`).
3. That is the **current phase**. Extract its section by marker (step 1).
4. Consistency check: if the Phase Map and the phase's `### Step Index` disagree
   (Phase Map says `Complete` but steps are open, or every step is `Complete`
   but the Phase Map row is not), flag the inconsistency and stop — do not run
   anything until the operator resolves which is true. One exception: the row is
   `In progress`, every step is `Complete`, and the latest execution row for that
   phase in the Session Log is `Partial` (ignore `Review` and `Checkpoint failed`
   rows). That is a pending validation retry, not an inconsistency: inspect the
   completed results, preserve the original **Baseline**, rerun the tests and the
   applicable Definition of Done, and finish the bookkeeping without
   reimplementing completed steps. Any other unexplained disagreement still
   stops. Existing Corrections stay mandatory on a retry.
5. Note the phase's **Model** from the Phase Map row.
6. If the phase block contains a heading whose text is `Blocking Questions`
   (any level, outside fenced code blocks), check each question under it before
   spawning. A question is answered when an answer or resolution is recorded
   beneath it. Ask the unanswered ones in the orchestrator, then record each
   answer under its question as `**Answer (YYYY-MM-DD):** <answer>`. Stop if a
   required answer is still missing. If a new blocking question arises during
   a retry, keep the completed steps as they are. A phase with no such heading
   skips this step. `/refactor-loop` runs this check itself before invoking
   this command, and stops rather than asking.
7. Record the baseline commit — see below.
8. Construct the prompt and run by model — see below.

If no eligible phase exists (all complete, or all remaining are blocked by incomplete deps):
report the state and stop. Do not run anything.

---

## Baseline commit

`/refactor-checkpoint` validates a phase by diffing the tree against the commit the
phase started from. That baseline can only be captured here, before any code moves —
afterwards there is no way to separate this phase's changes from the previous one's,
and the checkpoint falls back to reviewing the phase's own account of itself.

Run `git rev-parse HEAD`. In the current phase's header block — alongside
**Depends on**, **Model**, and **Files to modify** — set:

```text
**Baseline:** <sha>
```

Rules:

- If the field is absent, add it.
- If the field already holds a SHA, **leave it alone**. A phase being re-run after a
  failed checkpoint must keep its original baseline, or the diff loses everything the
  first attempt did and the checkpoint reviews half the work.
- If the working tree is dirty, say so in the report. The baseline then includes
  pre-existing uncommitted changes and the checkpoint's diff review will be noisy
  through no fault of the phase.

---

## Prompt construction

Assemble four parts in order:

### Part 0 — Shared context

Paste, in full, the marker-delimited shared sections: `shared:intent`,
`shared:hard-constraints`, `shared:definition-of-done` and `shared:design-map`. A
tracking file written before the Design Map existed has no `design-map` markers; paste
the other three and note the gap in your report rather than inventing a map.
Introduce them with:

> The following sections are reproduced in full from `.local/REFACTOR.<kebab>.md`.
> They are complete as given — do not reread the full tracking file. Narrow
> section reads and edits for required bookkeeping (Step Index, Phase Map,
> Session Log) and for the Design Map placement and follow-up updates are
> permitted. This overrides any instruction in the reproduced preamble that
> forbids opening that file.

The Design Map is the only view a phase agent gets of the project beyond its own files.
Without it, the agent places code by looking at its neighbors, which is how a refactor
ends up with a near-duplicate helper in every package it touched.

**Paste them; do not cite them.** A subagent told to "read §Hard Constraints" opens a
~90KB tracking file to retrieve ~500 tokens, and pulls every other phase's steps into
its context on the way past. Inlining them costs ~2k tokens and is the single
biggest lever on how much context a phase agent has left for its actual work. The same
applies to any other `.local/` document the preamble leans on: quote the passage, never
the section number.

Include the complete `## Test Command` section here too. It is never inside a
shared marker, so extract it separately: its heading and all content up to,
but excluding, the next level-2-or-higher heading outside a fenced code block,
or to end of file. A `# comment` line inside a fenced command block is not a
heading; ending there truncates the commands. At end of file do not drop the
last line, or a command is lost. If the file has no `## Test Command` section,
stop and report it: never infer a test command. Keep every command and
conditional validation rule. The agent must receive them without opening the
full tracking file.

### Part 1 — Standard Preamble

Copy verbatim from the phase's `### Standard Preamble` section.

### Part 2 — Phase assignment

Copy verbatim: the phase header and all its metadata (including continued
**Files to modify** lines and any ADR requirement), the `### Step Index`
table, every `### Step N.x` section in order (full content, all code blocks),
the phase's `### Corrections` section if present, and every heading inside the
phase markers whose text begins with `Definition of Done` (at any level), with
its full content. More than one such heading means the phase has
terminal-state variants; copy all of them. If the phase has a `Blocking
Questions` section, copy it with its recorded answers, so an answer given to the
orchestrator reaches the implementer. Find sections by Markdown boundaries (the
next heading of the same or higher level, or the phase end marker), ignoring
heading-looking text inside fenced code blocks. Verify each required part is
present before launching the agent. Missing required content is a stop; never
infer requirements or tests to fill the gap.

### Part 3 — Closing instructions

Append exactly as written, with `.local/REFACTOR.<kebab>.md` substituted for the
selected refactor's real tracking-file name so the subagent never has to resolve it:

> You are executing a complete refactor phase. Work through each step in the Step Index
> in order. If the phase has more than one `Definition of Done` heading
> (terminal-state variants), first decide which variant applies, from the
> conditions the phase already states, before running any step that variant
> excludes. If you cannot determine it, stop through the partial path below,
> naming the unresolved variant in the `Partial` row; never choose an
> exclusion to excuse a failure. Skip any step already marked `Complete` in the
> Step Index — verify its result exists in the code, or its explicit
> terminal-state exclusion is recorded in the Session Log Notes, rather than
> redoing it. For each remaining step, complete the implementation described in
> its section, then mark it `Complete` in the `### Step Index` table in
> `.local/REFACTOR.<kebab>.md`.
>
> If you must stop early (blocker, interruption, failing tests), do the partial
> bookkeeping before you return: keep finished steps `Complete`, leave the rest
> open, set this phase's Phase Map row to `In progress`, and append a `Partial`
> Session Log row naming the blocker. Never mark unfinished work `Complete`.
>
> If a `### Corrections` section is present, a previous run of this phase failed its
> checkpoint. Every item in it is mandatory scope on this run and must be fixed —
> including where it contradicts a Step Index row already marked `Complete`. Those
> marks are precisely what failed validation; treat the corrections as authoritative
> over them. Do not delete the section: the checkpoint removes it once it passes.
>
> **Place code for the project, not just the phase.** Before you add a function, type,
> constant, file or hand-maintained list entry, check the §Design Map Placement table,
> then search for an existing near-equivalent — the code graph's semantic search if the
> repo has one, then grep by behavior, not only by name. If something already does the
> job, extend or reuse it. Prefer extending an existing shape to adding a parallel one.
> If correct placement means changing a file outside **Files to modify** — extending a
> shared helper instead of copying it, exporting a constant instead of duplicating it —
> make that change, keep it minimal, and record it: add a §Design Map Placement row and
> a `placement: <file> — <reason>` entry in your Session Log note. Do not copy code to
> stay inside the file list. That restriction exists to stop unplanned work, not to
> force duplication, and the checkpoint accepts a recorded placement edit that matches
> the Design Map. If the right consolidation is bigger than this phase can absorb, make
> the local change and add the consolidation to §Design Map Follow-ups.
>
> After all steps are done:
>
> 1. Run the §Test Command reproduced in this prompt.
>    If tests fail, do not mark the phase complete: take the partial path above
>    (Phase Map `In progress`, `Partial` row), report the failure, and stop.
> 2. Satisfy the Definition of Done. When the phase has terminal-state variants,
>    the selected variant's checklist replaces the other phase checklists;
>    the shared Definition of Done and Hard Constraints still apply and cannot
>    be waived. Record a successful skip or exclusion as literal `Complete` in
>    the Phase Map and Session Log, naming the variant and each excluded
>    step's disposition (the step and the phase-defined reason) in the Session
>    Log Notes only, and write those Notes before relying on the `Complete`
>    mark. Mark an excluded step `Complete` only as satisfied by that
>    disposition; do not claim its implementation exists. Claim success only
>    after tests and the applicable Definition of Done pass. For a blocked or
>    partial result, preserve truthful step states and do not mark the phase
>    complete.
> 3. Append one row to `## Session Log`:
>    `| YYYY-MM-DD | Phase N — [name] | [model] | Complete | [one-line note] |`
>    Use `Partial` for blocked or partial execution, explaining why. A
>    successful skip/exclusion uses `Complete` with its disposition in Notes.
> 4. Create or update `.local/COMMIT-MSG.txt` — one running file describing the
>    **entire** uncommitted set, Conventional Commits form, body explaining the *why*.
>    Update the existing file rather than adding a second; change its top line to
>    encompass the accumulated work. No `Co-Authored-By` or any AI attribution. Never
>    run `git commit`, `git add`, or `git push`.
> 5. Do these four bookkeeping items as **tool calls, before you write any closing
>    prose.** Narrating "now I'll update the tracking file" without calling a tool
>    ends your turn and the phase lands with its code done and its bookkeeping
>    missing — the single most common way this command fails.
> 6. Do **not** run a markdown linter on `.local/REFACTOR.<kebab>.md`. It is a gitignored
>    generated file whose per-phase template repeats headings by construction, so
>    MD024 fires once per phase and can never be cleared. Chasing those warnings is
>    what consumed the turn that should have written items 2–4.
> 7. Return a brief synopsis: what was done, any blockers or open questions, and
>    the name + model of the next phase.

---

## Run by model

### Haiku, Sonnet, or Opus

Spawn a subagent using the Agent tool:

- `subagent_type`: `general-purpose`
- `model`: the phase's model (`haiku` / `sonnet` / `opus`)
- `description`: `Refactor phase [N] — [short name]`
- `prompt`: the full constructed prompt

Run in the **foreground** so the synopsis returns before you report to the user.

### Codex

Codex cannot be auto-spawned. Ensure `.local/.gitignore` exists (containing `*` and
`!.gitignore`), then write the full constructed prompt to
`.local/CODEX-PROMPT.<kebab>.md` for the user to paste into their Codex session.
Then output:

```text
═══════════════════════════════════════
 Phase N — [name]
 Model: Codex
═══════════════════════════════════════

Prompt written to .local/CODEX-PROMPT.<kebab>.md. Paste it into your Codex session.

When Codex finishes:
- Confirm tests pass.
- Confirm Step Index and Phase Map are updated in .local/REFACTOR.<kebab>.md.
- Run /refactor-checkpoint <kebab> to validate the Definition of Done.
═══════════════════════════════════════
```

Do not mark anything complete. Wait for the user to return.

---

## After the subagent returns (Haiku / Sonnet / Opus)

**First, classify the result before filling bookkeeping.** A result is blocked
or partial when the agent reported a blocker, was interrupted, left steps
unfinished, or the tests or the applicable Definition of Done fail, including
the orchestrator's own test rerun below failing after every step was done. A
missing or non-synopsis response is not proof of completion: inspect the real
step results and validation.

For a blocked or partial result:

- Keep verified completed steps `Complete`; leave unfinished steps open.
- Set the phase's Phase Map row to `In progress`.
- Write a `Partial` Session Log row with the blocker or validation failure.
  Check for an existing row for this attempt first, so the agent's own `Partial`
  row is not duplicated. The log is append-only: if the agent logged `Complete`
  but a rerun fails, append a later `Partial` row so the latest execution row
  for the phase is not successful.
- Set the index Status to `blocked` when blocked; otherwise retain it. Keep the
  Phases count equal to the completed rows in the Phase Map.
- Report the blocker or unfinished validation. Skip the successful-completion
  review, the new `**Reviewed:**` marker and the `active` status bump. Nothing
  is marked `Complete` without verified implementation or an authorized
  exclusion.
- An explicit refactor argument is required to resume a `blocked` index row.

**For successful completion, verify the bookkeeping — do not take the synopsis as evidence.** A subagent
can finish the code correctly and still skip every closing item it was given, so check
all four directly:

```bash
grep -n '^| N |' .local/REFACTOR.<kebab>.md          # Phase Map row says Complete
sed -n '/phase:N:start/,/phase:N:end/p' .local/REFACTOR.<kebab>.md | sed -n '/^### Step Index$/,/^### Step /p'
grep -n "Phase N" .local/REFACTOR.<kebab>.md | head  # a Session Log row exists
ls -la .local/COMMIT-MSG.txt
```

A returned message that is **not** a synopsis — a lint aside, a note about what it is
"about to do" — means the closing sequence was cut short; assume none of the four
landed and check every one. Only when the checks establish that the phase really
succeeded, fill in any missing completion bookkeeping yourself rather than
re-running the phase. Otherwise take the blocked or partial path above.

Re-run the phase's test command yourself too. If it fails, take the blocked or
partial path above. If its proof is one expensive integration
target, confirm it was not a cached result — a `(cached)` package line reports an
earlier run's timings and says nothing about this phase's edit.

**Then review the phase in a second subagent, and adjudicate the findings.** This happens
here, not at checkpoint time: the diff is at its largest and freshest the moment the
implementer stops, and everything caught here is a defect that never reaches the operator.
Skip it only when the phase produced no changes at all.

The reviewer must be a **new `general-purpose` subagent on `model: opus`, run in the
foreground**. Never reuse the implementing agent — not by `SendMessage`, not by asking it
to check its own work. An agent reviewing its own output re-reads the intent it had while
writing, so a comment that says the wrong thing still looks right to it; only a reader
without that memory sees what is actually on the page, which is the position every future
reader is in.

Give it `git diff <baseline>` plus untracked files, §Hard Constraints, §Design Map and
the phase's own requirements quoted inline, and the standing instructions: report only, never edit; read
changed files in full plus the surrounding code needed to judge them; cite the governing
ADR per finding or say none was found; check the phase's own edits for the defect class
the phase exists to remove, if it has one; check placement against the §Design Map — a new helper or constant that duplicates an existing
one, code in the wrong module, a copy made to stay inside **Files to modify**, an
unrecorded placement edit; verify a tool is actually unavailable before
reporting it so; write findings to `.local/REVIEW.md`; an empty report is a useful result,
so do not pad it.

Adjudicate every finding yourself under the same rules `/refactor-checkpoint` applies —
verify each against the tree, apply what survives, prove any new guard test red before
green, escalate a §Hard Constraint violation rather than silently patching it, and delete
`.local/REVIEW.md` once each is applied or dismissed with evidence. Record the
adjudication in the Session Log as one row of terse decision lines.

**One review round. Do not re-spawn a reviewer over your own fixes** — every fix is new
code, so that loop has no terminating condition. `/refactor-checkpoint`'s delta review
covers what you changed here; two rounds over shrinking surfaces is where the yield
flattens.

Then record it in the phase header, alongside **Baseline:**, so the checkpoint reviews
only what changes after this point:

```text
**Reviewed:** <sha>
```

Use `git rev-parse HEAD` when the tree is clean, `git stash create` when it is dirty, and
`dirty` if neither is available.

### Update the index

In `.local/REFACTOR.md`, edit this refactor's row: set Status to `active` (from
`planning`, if this was the first phase, or from `blocked` after a successful
explicit retry), and update the Phases column to `<completed> / <total>` from the
current `## Phase Map`.

Report to the user:

1. Which refactor and phase ran, and which model was used.
2. A 3–5 sentence synopsis of what was done.
3. Review outcome: findings by severity, how many applied, how many dismissed and why.
4. Any blockers or open questions either agent flagged.
5. The name and model of the next phase.

Then: **remind the user to run `/refactor-checkpoint` before advancing** (with this
refactor's kebab title if more than one is active).
Do not automatically invoke the next phase. Wait for `/refactor-next` to be called again.

---

## Error handling

- **Subagent fails, is blocked, or returns partial work**: classify it as
  described in "After the subagent returns". Keep steps the agent finished
  `Complete`, leave the rest open, set the Phase Map to `In progress`, write the
  `Partial` row, set the index `blocked` when blocked, and report. An explicit
  retry may rerun validation when all steps are done. Never mark unfinished work
  `Complete`.
- **Phase has no Step Index**: flag the inconsistency, do not run anything.
- **Dependency phases incomplete**: name which phases are blocking, stop.
- **All phases complete**: report done, state next action (PR, deploy, etc.).
