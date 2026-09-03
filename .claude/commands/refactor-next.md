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
   anything until the operator resolves which is true.
5. Note the phase's **Model** from the Phase Map row.
6. Record the baseline commit — see below.
7. Construct the prompt and run by model — see below.

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

Paste, in full, the three marker-delimited shared sections: `shared:intent`,
`shared:hard-constraints`, `shared:definition-of-done`. Introduce them with:

> The following three sections are reproduced in full from `.local/REFACTOR.<kebab>.md`.
> They are complete as given — **do not open that file.**

**Paste them; do not cite them.** A subagent told to "read §Hard Constraints" opens a
~90KB tracking file to retrieve ~500 tokens, and pulls every other phase's steps into
its context on the way past. Inlining all three costs ~1.1k tokens and is the single
biggest lever on how much context a phase agent has left for its actual work. The same
applies to any other `.local/` document the preamble leans on: quote the passage, never
the section number.

### Part 1 — Standard Preamble

Copy verbatim from the phase's `### Standard Preamble` section.

### Part 2 — Phase assignment

Copy verbatim: the phase header line, the **Files to modify** line, the `### Step Index`
table, every `### Step N.x` section in order (full content, all code blocks), and the
phase's `### Corrections` section if it has one.

### Part 3 — Closing instructions

Append exactly as written, with `.local/REFACTOR.<kebab>.md` substituted for the
selected refactor's real tracking-file name so the subagent never has to resolve it:

> You are executing a complete refactor phase. Work through each step in the Step Index
> in order. Skip any step already marked `Complete` in the Step Index — verify its
> result exists in the code rather than redoing it. For each remaining step, complete
> the implementation described in its section, then mark it `Complete` in the
> `### Step Index` table in `.local/REFACTOR.<kebab>.md`.
>
> If a `### Corrections` section is present, a previous run of this phase failed its
> checkpoint. Every item in it is mandatory scope on this run and must be fixed —
> including where it contradicts a Step Index row already marked `Complete`. Those
> marks are precisely what failed validation; treat the corrections as authoritative
> over them. Do not delete the section: the checkpoint removes it once it passes.
>
> After all steps are done:
>
> 1. Run the test command from `.local/REFACTOR.<kebab>.md` §Test Command.
>    Do not mark the phase complete if tests fail — report the failure and stop.
> 2. Mark the phase `Complete` in `## Phase Map` in `.local/REFACTOR.<kebab>.md`.
> 3. Append one row to `## Session Log`:
>    `| YYYY-MM-DD | Phase N — [name] | [model] | Complete | [one-line note] |`
>    Use `Partial` if any step was left incomplete, and explain why in the note.
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

**First, verify the bookkeeping — do not take the synopsis as evidence.** A subagent
can finish the code correctly and still skip every closing item it was given, so check
all four directly:

```bash
grep -n '^| N |' .local/REFACTOR.<kebab>.md          # Phase Map row says Complete
sed -n '/<!-- phase:N:start -->/,/<!-- phase:N:end -->/p' .local/REFACTOR.<kebab>.md | grep -A6 'Step Index'
grep -n "Phase N" .local/REFACTOR.<kebab>.md | head  # a Session Log row exists
ls -la .local/COMMIT-MSG.txt
```

A returned message that is **not** a synopsis — a lint aside, a note about what it is
"about to do" — means the closing sequence was cut short; assume none of the four
landed and check every one. Fill in whatever is missing yourself rather than re-running
the phase; the code is already done and a re-run risks undoing it.

Re-run the phase's test command yourself too. If its proof is one expensive integration
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

Give it `git diff <baseline>` plus untracked files, §Hard Constraints and the phase's own
requirements quoted inline, and the standing instructions: report only, never edit; read
changed files in full plus the surrounding code needed to judge them; cite the governing
ADR per finding or say none was found; check the phase's own edits for the defect class
the phase exists to remove, if it has one; verify a tool is actually unavailable before
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
`planning`, if this was the first phase), and update the Phases column to
`<completed> / <total>` from the current `## Phase Map`.

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

- **Subagent fails or returns partial work**: leave affected steps `Not started`, report
  what went wrong, suggest retry or manual investigation.
- **Phase has no Step Index**: flag the inconsistency, do not run anything.
- **Dependency phases incomplete**: name which phases are blocking, stop.
- **All phases complete**: report done, state next action (PR, deploy, etc.).
