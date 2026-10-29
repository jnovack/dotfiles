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
5. Print the plan — refactor, phase range to run, `--through`, `--max-fails`, test
   command, entry point (below) — and start. Do not wait for confirmation.

### Entry point

| State at start | Begin at |
| --- | --- |
| Every phase up to `--through` is `Complete`, the `--through` phase has a `Phase N — checkpoint` PASS/WARN row in the Session Log, and the tree is clean | Stop: nothing to do |
| No phase `Complete` yet | Step 6 |
| A phase `In progress` with a `### Corrections` section | Run `/refactor-next <kebab>` (it executes the Corrections), then step 2. The FAIL count starts at 0: it counts only failures observed inside this loop, never one inherited from before it started |
| The newest `Complete` phase already has a checkpoint PASS/WARN row, the tree is clean, and the next phase is `Not started` | Step 6 — its handoff was already committed |
| Anything else | Step 2 |

---

## The cycle

1. **(Entry only — see above.)**

2. **Checkpoint.** Run `/refactor-checkpoint <kebab>` with the Skill tool. Note the
   phase it validated (`PHASE`), its Overall result, and whether it retired the
   refactor. It also catches a phase whose agent was interrupted mid-run.

3. **On FAIL** — no Codex, no commit: the phase has not passed, and committing it
   would freeze unvalidated work into the next phase's baseline. Increment the FAIL
   count for `PHASE`. If it has reached `--max-fails`, stop. Otherwise run
   `/refactor-next <kebab>` (it executes the `### Corrections` section), then go to
   step 2.

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

   Run `/refactor-next <kebab>` with the Skill tool, then go to step 2. If the phase's
   Model is `Codex`, `/refactor-next` writes `.local/CODEX-PROMPT.<kebab>.md` instead
   of spawning an agent: run it yourself with the same `codex exec` shape as step 4
   (`-s workspace-write -o <sp>/codex-last.txt`, the prompt file piped as `-`,
   `run_in_background`), apply step 5's exit, scope and test checks to it, and do not
   commit before step 2's checkpoint has passed.

---

## Stop conditions

Stop on any of: `--through` reached; `--max-fails` consecutive FAILs of one phase;
Codex nonzero exit, blocker or scope violation; tests red after the handoff; a
failed commit; next phase blocked on an unmet dependency;
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
