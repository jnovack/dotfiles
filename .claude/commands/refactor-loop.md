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
execution, never a write to a live service. Every subagent this command dispatches,
every agent those spawn, and every Skill they run keeps the global rule.

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
| A phase `In progress` with a `### Corrections` section | Dispatch `/refactor-next <kebab>` (§Dispatching checkpoint and next; see §Around every `/refactor-next`; it executes the Corrections), then step 2. The FAIL count starts at 0: it counts only failures observed inside this loop, never one inherited from before it started |
| The newest `Complete` phase already has a checkpoint PASS/WARN row, the tree is clean, and the next phase is `Not started` | Step 6 — its handoff was already committed |
| Anything else | Step 2 |

At entry, a phase whose latest execution row (ignoring `Review` and
`Checkpoint failed` rows) is `Partial` is an unresolved implementer blocker or
partial run: stop, even when the phase has Corrections. Only an ordinary checkpoint
failure with Corrections keeps the retry in the table above.

---

## Dispatching checkpoint and next

Every `/refactor-checkpoint` and `/refactor-next` this loop runs (the Entry point
Corrections row and steps 2, 3 and 6) is dispatched to a fresh subagent, never run
in this session. Inline runs reload about 55KB of command text per cycle and pile
diffs and review reports into the loop's context (about 126k tokens by phase 5 on
2026-11-09), which degrades late-run judgment. A fresh subagent per command keeps
this session to gates, result lines and commits.

### Before each dispatch: target and baseline

1. Run the gates first: the §Phase safety gate before every dispatch, plus both
   "Before" checks of §Around every `/refactor-next` for a `/refactor-next`.
   Prepare nothing below until they pass.
2. Select `EXPECTED_PHASE` from disk with the invoked command's own rules.
   - Checkpoint: the phase of the latest Session Log row whose Status is `Complete`
     or `Partial`, ignoring `Review` and `Checkpoint failed` rows. A Corrections
     retry leaves its phase `In progress` behind an older `Complete` execution row,
     so never select this target from Phase Map status alone.
   - Next: the first Phase Map row that is not `Complete` and whose dependencies
     are all `Complete`, which is the `In progress` phase at the Corrections entry
     and the step 3 retry.
3. Record the Session Log baseline. Save its data rows to a scratch file for the
   unchanged-prefix check and keep their count as `BASE`. A first execution can
   legitimately start with zero rows: `grep` then matches nothing and exits 1
   (`grep -c` prints `0`), which is a valid, empty baseline. A missing tracking file
   or `## Session Log` heading is an extraction failure and stops.
4. Before a `/refactor-next` dispatch whose `EXPECTED_PHASE` has Model `Codex` in
   the Phase Map, move any existing `.local/CODEX-PROMPT.<kebab>.md` to a uniquely
   named scratch backup (never delete it), then require the canonical path absent.
   An older prompt must not satisfy the freshness check below.

`<sp>` is the session scratchpad, as in step 4. Substitute every placeholder before
running; `<BASE>` and `<BASE+1>` are computed integers, not shell syntax:

```bash
# Baseline (before dispatch)
sed -n '/^## Session Log/,/^## /p' .local/REFACTOR.<kebab>.md | grep '^| [0-9]' > <sp>/session-log-base.<kebab>.txt
sed -n '/^## Session Log/,/^## /p' .local/REFACTOR.<kebab>.md | grep -c '^| [0-9]'
mv -n .local/CODEX-PROMPT.<kebab>.md <sp>/CODEX-PROMPT.<kebab>.<YYYYmmddHHMMSS>.md
test ! -e .local/CODEX-PROMPT.<kebab>.md

# After dispatch: old rows unchanged (exit 0), then the new rows
sed -n '/^## Session Log/,/^## /p' .local/REFACTOR.<kebab>.md | grep '^| [0-9]' | head -n <BASE> | diff <sp>/session-log-base.<kebab>.txt -
sed -n '/^## Session Log/,/^## /p' .local/REFACTOR.<kebab>.md | grep '^| [0-9]' | tail -n +<BASE+1>

# The same two reads against the archive once the tracking file is gone
sed -n '/^## Session Log/,/^## /p' .local/completed/REFACTOR.<kebab>.completed.md | grep '^| [0-9]' | head -n <BASE> | diff <sp>/session-log-base.<kebab>.txt -
sed -n '/^## Session Log/,/^## /p' .local/completed/REFACTOR.<kebab>.completed.md | grep '^| [0-9]' | tail -n +<BASE+1>

# Disk checks named in the table below
test -f .local/CODEX-PROMPT.<kebab>.md
test -f .local/completed/REFACTOR.<kebab>.completed.md
sed -n '/^## Phase Map/,/^## /p' .local/REFACTOR.<kebab>.md
```

Run the `mv` and the `test ! -e` only for the Codex case in item 4, and the `mv`
only when the prompt file exists.

### Dispatch

Use the Agent tool with `subagent_type: general-purpose` and `model: opus`, in the
foreground. Never use the `fork` subagent type, and never run either command with
the Skill tool in this session. Pass this prompt, verbatim except the placeholders:

```text
Invoke the Skill tool with skill "<refactor-checkpoint|refactor-next>" and args "<kebab>", and follow that command to its end in this repository.
- You run inside /refactor-loop with no operator. Never ask a question; if the command would need an answer, stop and report it in the result line.
- The command spawns its own subagents (reviewer, implementer). If you cannot spawn one, stop and report it. Never review or implement inline yourself.
- Do not run git add, git commit, git autocommit, git push, codex, or anything against a live service.
- Ignore the command's closing advice to the operator (which command to run next, pasting a Codex prompt). Do not act on it.
- Return at most ten summary lines, including blockers and material next-plan repairs; omit raw diffs and review reports.
- End your reply with exactly one line in this grammar, as the last line:
  LOOP-RESULT checkpoint phase=<N> overall=<PASS|WARN|FAIL> retired=<yes|no>
  LOOP-RESULT next phase=<N> outcome=<complete|partial|blocked|no-execution|codex-prompt>
  LOOP-RESULT stop reason=<one line>
```

The subagent's summary and result line are the only command output this session
sees; no later step relies on the command's own text.

### After each dispatch: verify on disk, then act

The tracking file is `.local/REFACTOR.<kebab>.md`, or
`.local/completed/REFACTOR.<kebab>.completed.md` once a checkpoint has retired it;
the index cannot confirm retirement alone, because retirement removes its row.

1. Parse the last non-empty line of the reply. It must match one of the three
   `LOOP-RESULT` forms exactly, its form must be the dispatched command's
   (`checkpoint` or `next`) or `stop`, and a checkpoint line with `overall=FAIL`
   must say `retired=no`. Anything else stops.
2. Require the old rows to remain an unchanged prefix (the `diff` above exits 0)
   and the returned `phase` to equal `EXPECTED_PHASE`. Otherwise stop.
3. Read the new rows (`tail -n +<BASE+1>`) and apply the table. Match the phase
   cell on the exact `Phase <N> —` prefix, so `Phase 1` never matches `Phase 10`,
   and inspect cell values, not these words elsewhere in Notes. Only rows after
   `BASE` count as fresh evidence; an older row never satisfies a check.

| Result line | Required on disk | Then |
| --- | --- | --- |
| `checkpoint … overall=PASS\|WARN` | A fresh row with Status `Review` whose phase cell is exactly `Phase <N> — checkpoint` and whose Notes start with the same verdict followed by `;`. Review adjudication and next-plan audit rows cannot satisfy this. The Phase Map row and every Step Index row of the phase are `Complete` and its `### Corrections` is gone. `retired=yes` also requires the live tracking file absent, the archive present, every Phase Map row `Complete` and the index row absent; `retired=no` requires the live tracking file and an active index row | Step 4 |
| `checkpoint … overall=FAIL retired=no` | A fresh row whose phase cell starts `Phase <N> —` with Status exactly `Checkpoint failed`; the phase `In progress` in the Phase Map, a `### Corrections` section present and the index row `blocked` | Step 3 |
| `next … outcome=complete` | The latest fresh execution row for the phase (ignore `Review` and `Checkpoint failed`) is `Complete`, so a later `Partial` fails this check. The Phase Map row and every Step Index row are `Complete`, the index row is active with a Phases count equal to the completed Phase Map rows, and the summary reports no blocker | Step 2 |
| `next … outcome=codex-prompt` | The phase's Model is `Codex`; the canonical prompt was absent before dispatch and now exists and contains the selected phase's full `## Phase <N> — <title>` header line, matched as a whole line (`grep -Fx`) so `Phase 1` never matches `Phase 10`. No execution row is required yet. Keep `BASE` for the post-Codex execution checks | Step 6: run Codex. Entry or step 3 retry: stop with the prompt path |
| `next … outcome=partial\|blocked\|no-execution` | Inspect any fresh rows, the summary and the index for the stop reason; missing bookkeeping never permits continuing | Stop |
| `stop …`, or no parseable `LOOP-RESULT` last line | — | Stop, quoting the line or the subagent's last paragraph |

Missing or contradictory required evidence stops the loop. The loop never repairs
the command's bookkeeping to make a check pass and never invents an execution row.
Set `PHASE` only after confirming the preselected target. The commands' own
skip-review paths stay valid: an inability to spawn stops only when a spawn was
required, not when the command legitimately skips it.

---

## The cycle

1. **(Entry only — see above.)**

2. **Checkpoint.** First rerun the §Phase safety gate on the phase the checkpoint will
   validate (the newest `Complete` or `Partial` phase): its Test Command, DoD and
   repair commands are part of the Commands inventory, and Corrections, operator edits
   or an earlier handoff's plan repairs may have changed them since preflight. A
   failure stops the loop with the `FAIL` lines. Then dispatch
   `/refactor-checkpoint <kebab>` (§Dispatching checkpoint and next). Take `PHASE`,
   its Overall result, and whether it retired the refactor from the verified result
   line. It also catches a phase whose agent was interrupted mid-run.

3. **On FAIL** — no Codex, no commit: the phase has not passed, and committing it
   would freeze unvalidated work into the next phase's baseline. Increment the FAIL
   count for `PHASE`. If it has reached `--max-fails`, stop. Otherwise dispatch
   `/refactor-next <kebab>` (§Dispatching checkpoint and next; see §Around every
   `/refactor-next`; it executes the `### Corrections` section), then go to step 2.

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

   Dispatch `/refactor-next <kebab>` (§Dispatching checkpoint and next; see §Around
   every `/refactor-next`). For a Claude-model execution, apply its return checks and
   then go to step 2. If the phase's Model is `Codex`, `/refactor-next` writes
   `.local/CODEX-PROMPT.<kebab>.md` instead
   of spawning an agent: run it yourself with the same `codex exec` shape as step 4
   (`-s workspace-write -o <sp>/codex-last.txt`, the prompt file piped as `-`,
   `run_in_background`), apply step 5's exit, scope and test checks to it, and do not
   commit before step 2's checkpoint has passed. Writing the prompt file is not phase
   execution: also run the §Around every `/refactor-next` return check after `codex exec`
   returns, before going to step 2 or any commit. Those checks, and the
   `next … outcome=complete` disk requirements, use the `BASE` recorded before the
   dispatch, so the Codex run must append a fresh `Complete` row for the phase.

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
  select (`EXPECTED_PHASE`, §Dispatching checkpoint and next), by its markers
  (`sed -n '/phase:N:start/,/phase:N:end/p'`), and check the output is non-empty; a
  tracking file without phase markers extracts nothing and stops. If it
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
- **After: blocked or partial execution.** Inspect the actual run's report (the
  dispatched subagent's `LOOP-RESULT` line and summary), the latest
  execution Session Log row for that phase (ignoring `Review`, `Checkpoint failed` and
  older attempt rows, so a successful retry supersedes an old `Partial` row) and the
  index. A blocked or partial result stops before checkpoint, handoff, commit or
  another phase, even when `codex exec` exited 0. At step 6's Codex branch, these
  checks run on the Codex execution result, not on prompt-file generation.
- **After: no execution.** `/refactor-next` also stops before launching anything:
  missing prompt content, a Phase Map/Step Index inconsistency, no eligible phase. That
  leaves no new execution row for the target phase, so the check above sees the previous
  phase's `Complete` row. If no execution row for the target phase appeared after the
  dispatch baseline (`BASE`, §Dispatching checkpoint and next), stop. Continuing would
  re-checkpoint and re-commit the previous phase instead.

---

## Stop conditions

Stop on any of: `--through` reached; `--max-fails` consecutive FAILs of one phase;
Codex nonzero exit, blocker or scope violation; tests red after the handoff; a
failed commit; a phase failing `plan-loop-check --phase` (preflight, before a
checkpoint or before any `/refactor-next`) or the checker missing; an unanswered
Blocking Question; a blocked, partial or unexecuted
`/refactor-next` result; next phase blocked on an unmet dependency;
`codex` missing or its flags changed; a preflight failure; the refactor retired; a
dispatched subagent's `LOOP-RESULT stop`, missing or unparseable result line, result
for the wrong command or a phase other than the preselected one, changed Session Log
rows before `BASE`, or result whose required fresh disk evidence is missing or
contradictory; or any step
that would need an action this file does not list. Never improvise past a
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
