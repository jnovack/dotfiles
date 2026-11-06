---
description: Run the unattended refactor loop — checkpoint, Codex handoff, commit, next phase — until a phase limit or a stop condition
argument-hint: [<refactor>] [--through N] [--max-fails 2]
---

# /refactor-loop

Drive `/refactor-checkpoint`, the Codex `$refactor-handoff` skill, `git autocommit`
and `/refactor-next` in a cycle, phase after phase, with no operator in the loop. It
is built to run unattended (for example under `CronCreate`), so it never asks a
question: anything it cannot decide from this file is a **stop**, not a guess.

---

## Step 0 — Select the refactor and parse flags

`.local/REFACTOR.<kebab>.md` is a refactor's tracking file; `.local/REFACTOR.md` is
the **index**.

- **Kebab argument given** — use `.local/REFACTOR.<arg>.md`. If it does not exist,
  stop.
- **No kebab argument** — take the single index row whose Status is `planning` or
  `active`. None → "no refactor in progress"; more than one → list them and stop.
  An unattended run cannot answer "which one?", so it requires the argument.
- **Back-compat** — if `.local/REFACTOR.md` contains `## Phase Map` or `## Intent`,
  it is the old single-file format; stop and tell the user to migrate.

Flags:

- `--through N` — the last phase this run may execute. Default: the final phase
  minus one. The final phase needs the operator, so it runs only when `--through`
  names it explicitly.
- `--max-fails K` — consecutive checkpoint FAILs of one phase before stopping.
  Default `2`.

---

## Permission exception: `git autocommit`

Invoking `/refactor-loop` is the operator's grant to run `git autocommit` (the alias
`git add -A && git commit -F .local/COMMIT-MSG.txt && rm .local/COMMIT-MSG.txt`) at
step 5, and only there. It overrides the global "do not run `git add`/`git commit`"
rule for that one call and for nothing else: no other `git add`/`commit`/`amend`, no
`--no-verify`, never `git push`, never `make docker-push`, never Playwright
execution, never a write to a live service. Every subagent and Skill this command
invokes keeps the global rule.

---

## Preflight

Run once, before the first cycle:

1. `git status --porcelain`. The tree must be clean, or dirty only with this
   refactor's own uncommitted phase work (files in the current phase's **Files to
   modify** plus `.local/COMMIT-MSG.txt`). Anything else → stop: `git autocommit`
   runs `git add -A` and would sweep unrelated operator edits into a phase commit.
2. The tracking file exists and has a `## Phase Map`.
3. `command -v codex` succeeds, and `codex exec --help` lists both `-s` and `-o`. If
   either is missing, stop rather than guess at flags.
4. Read the Phase Map and Test Command by marker, never the whole file — it grows
   to ~90KB:

   ```bash
   sed -n '/^## Phase Map/,/^## /p' .local/REFACTOR.<kebab>.md
   sed -n '/^## Test Command/,/^## /p' .local/REFACTOR.<kebab>.md
   ```

   No `## Test Command` → use `go test ./...`.
5. **Loop safety.** `test -x ~/.claude/bin/plan-loop-check` must succeed; if not,
   stop (a missing gate is not a pass). Then, with the Phase Map and the entry point
   below, build the list of phases this run may touch and gate each one (§Phase
   safety gate), without duplicates:
   - the **entry phase**: the phase whose checkpoint or repair work runs first,
     even when it is already `Complete` and only awaiting its checkpoint, or the
     `In progress` phase with Corrections (its `/refactor-next` retry runs first);
   - then every incomplete phase this run may execute, up to `--through`.

   If the first phase in that list fails, stop and quote every `FAIL` line. If only
   a later phase fails, report its `FAIL` lines in the plan printout and let the loop
   finish the earlier safe phases; step 6 gates it again and stops there. A true
   no-work entry still stops, with no phase to gate. A legacy phase without the
   `**Unattended:**` field or a `### Commands` subsection fails with the checker's
   corrective message: the loop never adds the fields or guesses commands, and
   `--through` cannot override a `no`.
6. Print the plan — refactor, phase range to run, `--through`, `--max-fails`, test
   command, entry point (below), and the preflight safety results — and start. Do
   not wait for confirmation.

### Phase safety gate

Run it as one line from the repo root:

```bash
~/.claude/bin/plan-loop-check --phase <N> .local/REFACTOR.<kebab>.md
```

Exit 0 (`PASS  <kebab>#<N>`) lets the call proceed. Anything else is a stop that
quotes the checker's `FAIL` lines verbatim. The gate is a policy lint of the phase's
shell fences against the deny and ask rules; passing it does not authorize a denied
or live operation. The loop never edits a phase's `**Unattended:**` field, its
`### Commands` section or its Corrections to get past the gate. When the refactor
has retired, the file is `.local/completed/REFACTOR.<kebab>.completed.md`, and there
is no successor to gate.

### Entry point

| State at start | Begin at |
| --- | --- |
| Every phase up to `--through` is `Complete`, the `--through` phase has a `Phase N — checkpoint` PASS/WARN row in the Session Log, and the tree is clean | Stop: nothing to do |
| No phase `Complete` yet | Step 6 |
| A phase `In progress` with a `### Corrections` section | Run `/refactor-next <kebab>` (see §Around every `/refactor-next`; it executes the Corrections), then step 2. The FAIL count starts at 0: it counts only failures observed inside this loop, never one inherited from before it started |
| The newest `Complete` phase already has a checkpoint PASS/WARN row, the tree is clean, and the next phase is `Not started` | Step 6 — its handoff was already committed |
| Anything else | Step 2 |

At entry, a phase whose latest execution row (ignoring `Review` and
`Checkpoint failed` rows) is `Partial` is an unresolved implementer blocker or
partial run: stop, even when the phase has Corrections. Only an ordinary checkpoint
failure with Corrections keeps the retry in the table above.

---

## The cycle

1. **(Entry only — see above.)**

2. **Checkpoint.** First rerun the §Phase safety gate on the phase the checkpoint will
   validate (the newest `Complete` or `Partial` phase): its Test Command, DoD and
   repair commands are part of the Commands inventory, and Corrections, operator edits
   or an earlier handoff's plan repairs may have changed them since preflight. A
   failure stops the loop with the `FAIL` lines. Then run
   `/refactor-checkpoint <kebab>` with the Skill tool. Note the
   phase it validated (`PHASE`), its Overall result, and whether it retired the
   refactor. It also catches a phase whose agent was interrupted mid-run.

3. **On FAIL** — no Codex, no commit: the phase has not passed, and committing it
   would freeze unvalidated work into the next phase's baseline. Increment the FAIL
   count for `PHASE`. If it has reached `--max-fails`, stop. Otherwise run
   `/refactor-next <kebab>` (see §Around every `/refactor-next`; it executes the
   `### Corrections` section), then go to step 2.

4. **On PASS or WARN** — reset the FAIL count. If the checkpoint retired the
   refactor, the tracking file now lives at
   `.local/completed/REFACTOR.<kebab>.completed.md`: use that path as the tracking
   file below and omit `NEXT_PHASE` (there is no successor). Codex still runs, then
   step 5 verifies and commits, then stop.

   Snapshot `git status --porcelain` and `git diff --stat` (keep the
   output in context), then launch the Codex handoff with `run_in_background` —
   Codex runs routinely outlast the foreground Bash timeout. `<sp>` is the session
   scratchpad directory from the system prompt (`.local/` if the session lists
   none; never `/tmp`). Single line, bare `codex`:

   ```bash
   codex exec -s workspace-write -o <sp>/codex-last.txt '$refactor-handoff PHASE=<PHASE> NEXT_PHASE=<PHASE+1> refactor=<kebab> (tracking file .local/REFACTOR.<kebab>.md). Run unattended; do not ask questions, and do not run git add/commit/push or any live service.' > <sp>/codex-out.txt 2>&1
   ```

   Omit `NEXT_PHASE=…` when `PHASE` equals `--through` or is the final phase. Wait
   for the exit notification; do not poll the output files and start nothing else
   meanwhile.

5. **Verify, then commit.** Codex's summary is a claim, not evidence.
   - Exit status nonzero → stop.
   - Read `<sp>/codex-last.txt`. A reported blocker, or a phase-gate refusal → stop.
   - Compare `git status --porcelain` and `git diff --stat` with the snapshot. Every
     file Codex changed must belong to `PHASE` (its **Files to modify**, its tests
     and docs, or a recorded `placement:` edit). The next phase's Phase Map row must
     still be `Not started`. Otherwise → stop.
   - Run the Test Command yourself. Not green → stop.
   - `.local/COMMIT-MSG.txt` exists → `git autocommit`. A failed commit (for example
     a hook rejection) → stop. Tree clean and no message → nothing to commit;
     continue. Tree dirty and no message → stop: advancing would fold this phase's
     work into the next phase's baseline.

   The commit lands here — after Codex, because the handoff legitimately changes
   code, and before the next phase, so that phase's **Baseline** is a clean HEAD
   and its checkpoint diff holds only its own work.

6. **Next phase.** Find the next eligible phase in the Phase Map (first non-`Complete`
   row whose dependencies are all `Complete`).
   - It is past `--through` → stop: limit reached.
   - None eligible (dependencies incomplete) → stop: blocked.

   Run `/refactor-next <kebab>` with the Skill tool (see §Around every
   `/refactor-next`). For a Claude-model execution, apply its return checks and
   then go to step 2. If the phase's Model is `Codex`, `/refactor-next` writes
   `.local/CODEX-PROMPT.<kebab>.md` instead
   of spawning an agent: run it yourself with the same `codex exec` shape as step 4
   (`-s workspace-write -o <sp>/codex-last.txt`, the prompt file piped as `-`,
   `run_in_background`), apply step 5's exit, scope and test checks to it, and do not
   commit before step 2's checkpoint has passed. Writing the prompt file is not phase
   execution: also run the §Around every `/refactor-next` return check after `codex exec`
   returns, before going to step 2 or any commit.

### Around every `/refactor-next`

Every `/refactor-next <kebab>` this loop runs (Entry point, step 3 and step 6) is
wrapped by these checks.

- **Before: phase safety.** Run the §Phase safety gate on the phase `/refactor-next`
  will select (same selection), on every invocation: the Corrections entry row, the
  step 3 FAIL retry (Corrections written by the checkpoint just now may add commands)
  and the step 6 next phase, Codex-assigned phases included. A failure stops the
  loop, quoting the `FAIL` lines, before anything launches, so an unsafe retry
  cannot run, be checkpointed or be committed.
- **Before: Blocking Questions.** Extract the phase block that `/refactor-next` will
  select (same selection and legacy marker fallback), by its markers
  (`sed -n '/phase:N:start/,/phase:N:end/p'`), and check the output is non-empty. If it
  has a heading whose text is `Blocking Questions` (any level, outside fenced code
  blocks), and any question under it has no answer or resolution recorded beneath it →
  stop, quoting the question. Never ask it: `/refactor-next` run directly would ask, and
  this loop cannot. A phase with no such heading is unaffected.
- **Codex prompt dispatch.** At step 6, successful generation of the selected
  phase's Codex prompt is pending execution, not an unexecuted failure or a
  completed phase. Defer both execution-return checks below until that branch's
  `codex exec` has finished. A failure to generate the required prompt still
  stops. The Corrections entry and step 3 retry do not acquire a new Codex launch
  path: if they return only a manual Codex prompt, stop and report its path for
  the operator rather than checkpointing an older execution.
- **After: blocked or partial execution.** Inspect the actual run's report, the latest
  execution Session Log row for that phase (ignoring `Review`, `Checkpoint failed` and
  older attempt rows, so a successful retry supersedes an old `Partial` row) and the
  index. A blocked or partial result stops before checkpoint, handoff, commit or
  another phase, even when `codex exec` exited 0. At step 6's Codex branch, these
  checks run on the Codex execution result, not on prompt-file generation.
- **After: no execution.** `/refactor-next` also stops before launching anything:
  missing prompt content, a Phase Map/Step Index inconsistency, no eligible phase. That
  leaves no new execution row for the target phase, so the check above sees the previous
  phase's `Complete` row. If no execution row for the target phase appeared during this
  run, stop. Continuing would re-checkpoint and re-commit the previous phase instead.

---

## Stop conditions

Stop on any of: `--through` reached; `--max-fails` consecutive FAILs of one phase;
Codex nonzero exit, blocker or scope violation; tests red after the handoff; a
failed commit; a phase failing `plan-loop-check --phase` (preflight, before a
checkpoint or before any `/refactor-next`) or the checker missing; an unanswered
Blocking Question; a blocked, partial or unexecuted
`/refactor-next` result; next phase blocked on an unmet dependency;
`codex` missing or its flags changed; a preflight failure; the refactor retired; or
any step that would need an action this file does not list. Never improvise past a
stop.

Before ending, file every deferred item and open decision in `.local/TODO.md` via
the `todo-add` skill, then report:

```text
═══════════════════════════════════════
 Refactor loop — <kebab>
═══════════════════════════════════════
 Phases completed this run   <list, with commit SHAs>
 Last checkpoint             Phase N — PASS / WARN / FAIL
 Stop reason                 <condition, with the evidence>
 Tree                        clean / dirty — <what is uncommitted>
 TODO IDs filed              <ids, or none>
 Next                        <command for the operator>
═══════════════════════════════════════
```

---

## Scheduling

To fire it once at a chosen time, use `CronCreate` with `recurring: false`, a cron
pinned to that minute, hour, day and month, and this prompt:

```text
/refactor-loop <kebab> --through <N>
```

The job is session-only (gone when Claude exits) and fires only while the REPL is
idle, so leave the session open and idle.
