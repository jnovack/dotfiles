---
description: Run the unattended todo loop — next ready item, checkpoint, commit, repeat — until the queue drains, a limit, or a stop condition
argument-hint: [--max-items N] [--max-fails 2] [--stall-minutes 20] [--check]
---

# /todo-loop

Drive `/todo-next` and `/todo-checkpoint` item after item, strictly in series: one
item is implemented, reviewed, checkpointed and committed before the next one
starts, so every item builds on a clean, committed HEAD. It is built to run
unattended (for example under `CronCreate`), so it never asks a question: anything
it cannot decide from this file is a **stop**, not a guess.

**Why it is shaped this way.** On 2026-10-21 an overnight chain dispatched its
first implementer as a background agent and ended its turn to await the completion
notice. The agent ran a compound shell command, hit a permission prompt
(`acceptEdits` mode), and waited seven hours for an answer nobody was there to
give. Nothing noticed. Two rules below exist because of that night: preflight
refuses a permission mode that prompts, and every stop sends a push notification.
The per-agent watchdog added after that night was dropped on 2026-11-11, when the
commands moved into dispatched subagents (see §Dispatching next and checkpoint).

On 2026-10-30 the loop ran in auto mode and still stopped at its first checkpoint. A
plan's gate said "in a disposable scratch copy" without naming a command. The agent
chose `rsync`, which the global deny list blocks in every mode. Every plan the run will
touch now passes `~/.claude/bin/plan-loop-check` before the loop relies on it, and
`--check` reports exactly where an unattended run would stop.

---

## Step 0 — Parse flags

- `--max-items N` — items to retire in this run. Default: no limit; run until the
  queue has no eligible `ready` item.
- `--max-fails K` — consecutive checkpoint FAILs of one item before stopping.
  Default `2`, which allows one retry against the `## Corrections` section.
- `--stall-minutes M` — transcript silence after which `todo-agent-live` counts an
  earlier run's agent as no longer live. Default `20`.
- `--check` — run Preflight only, print its result and the planned queue, and change
  nothing. Run it before scheduling, so a failing check surfaces while you are still
  at the keyboard rather than at 3am.

`<sp>` below is the session scratchpad directory from the system prompt. No
scratchpad listed → stop: the permission-mode and liveness checks take it as their
argument.

---

## Unattended rules

- Never use AskUserQuestion and never wait for input.
- Only `ready` items run. Never mark an item `ready`, and never run a `planned`,
  `spec'd` or `raw` item: `ready` is the operator's approval and the loop cannot
  give it.
- Never edit `.local/TODO.md` statuses by hand. The todo skills own them.
- **The loop never commits.** `/todo-checkpoint` runs `git autocommit` on PASS or
  WARN, as its own file instructs; that is the only commit in a run. Never run
  `git add`, `commit`, `push`, `reset`, `checkout`, `stash` or `clean`, never write
  to a live service, and never deploy. The one exception is exactly
  `git stash create`, in two contexts only: `/todo-next` recording its `reviewed:`
  marker, and validation probes the selected item's spec and plan explicitly require,
  run in a freshly created disposable scratch clone, never the live repository. It
  writes an unreferenced commit object and changes no working-tree content, staged
  entry, ref or stash list, so a ban on it only forces a needless second full review.
  Every other `stash` form stays forbidden, and the stop procedure's "do not stash"
  is unchanged.
- Never work around a failing test, a denied command, or a spec Constraint. Stop.
- Do not wrap this in `/loop` or schedule wakeups. Dispatch results and completion
  notices resume the loop.

---

## Preflight

Run once, before the first cycle. Any failure is a stop (with `--check`, a report).

1. **Permission mode.** Run `~/.claude/bin/claude-permission-mode <sp>`.
   - `auto`, `bypassPermissions` or `dontAsk` → continue.
   - `default`, `acceptEdits` or `plan` → stop. Name the mode and tell the operator
     to restart the session in auto mode. These modes prompt for any command
     outside the allowlist, and an unattended prompt is a stall.
   - `unknown` (no mode-bearing record found) → log a `WARN` line and continue. The
     observed cause is a session whose only prompt was a slash command, which has
     been seen to record no mode; a changed transcript format or a missing
     transcript gives the same result. The helper reports the newest *recorded*
     mode, not the live Shift+Tab state, so it can be stale. It is rechecked when
     each dispatch returns (see §Dispatching next and checkpoint).
     **Warning budget:** at most one unknown `WARN` per loop run, this one included.
     Later unknown results continue silently, except as mode detail in an error
     notification. Reset the budget at the run's `BEGIN`; after compaction
     restore it from this run's log records, as described by the completion check.
     For an actual run, write its `BEGIN` before its first unknown `WARN`. With
     `--check`, print the diagnostic only: do not append `BEGIN` or `WARN` or
     change the log; the preflight-only check remains read-only.
   - Helper missing or not executable → stop.
2. **Helpers.** `~/.claude/bin/claude-permission-mode`, `~/.claude/bin/plan-loop-check`
   and `~/.claude/bin/todo-agent-live` exist and are executable.
3. **No other scheduled jobs.** Run `CronList`. Any job in this session → stop and
   list it. On 2026-10-21 a 5:25am `git autocommit` job shared the session with the
   chain. If an item had been half-written at 5:25, that job would have committed it.
   The one-shot that launched this run has already fired and is gone.
4. **Tracker.** `.local/TODO.md` exists, and `git check-ignore -q .local/TODO.md`
   succeeds. If `.local/` is not ignored, `git autocommit` would commit the tracker.
5. **Branch.** `git branch --show-current` prints a name (not a detached HEAD).
   Report it.
6. **Tree and entry point.** `git status --porcelain`, then choose the entry point
   from the table below.
7. **Docker**, only when a queued item needs it: if any eligible `ready` item's plan
   names a Docker-backed command (`docker`, `docker compose`, an `e2e` build tag,
   testcontainers), `docker info` must succeed.
8. **Loop safety.** Run `~/.claude/bin/plan-loop-check` on the plan of every item this
   run would touch, in run order: the entry-point item when it is not Step 1, then the
   eligible `ready` items in queue order, up to `--max-items`. A plan that fails names
   a command the permission settings deny or prompt for, a missing `## Commands`
   section, or a declared `unattended: no`. Any of these stops the run at that item.
   - The **first** item fails → stop, quoting every `FAIL` line.
   - A **later** item fails → the run is not fully unattended. Without `--check`,
     continue: the cycle's Select step re-checks each item, so the loop retires the
     items before it and stops there. A checkpoint's fix-ahead may repair the plan in
     the meantime.
9. **Print the plan** and start. Do not wait for confirmation. Include the mode, the
   flags, the entry point, and the items in run order up to `--max-items`, each with its
   loop-safety result. With `--check`, print the plan and stop here, ending with exactly
   one verdict:
   - `READY TO SCHEDULE — <N> items, all loop-safe`
   - `NOT FULLY UNATTENDED — stops before <ID> after at most <K> items: <FAIL reasons>.
     Fix: /todo-plan <ID>, or schedule with --max-items <K>`
   - `NOT READY — <failing preflight check>`

   Do not soften a non-ready verdict. The operator schedules on the strength of this
   line.

### Entry point

When a `done` or `in progress` row exists, run the liveness check below first. Then
take the first row of this table that matches.

| State at start | Begin at |
| --- | --- |
| No `done` or `in progress` row, and the tree is clean | Step 1 |
| More than one `done` or `in progress` row | Stop and list them |
| One `done` or `in progress` row, and the liveness check finds a live agent for it | Stop. Another session is still working the item, and taking it over would race that agent's writes to the tree |
| One `done` or `in progress` row whose last line in the log is a `STALL` | Stop. An earlier run paged the operator about that agent, which may still be waiting for their answer. Once it is gone, the operator runs `/todo-checkpoint <id>` by hand (only logs written by an older, stall-paging version of this loop contain `STALL`) |
| Exactly one `done` row. The tree is clean, or dirty only with that item's work (files its plan's Steps or Placement name, their tests and docs) | Step 3 for that ID. Its implementer finished but was never checkpointed |
| Exactly one `in progress` row whose plan carries `## Corrections` | Step 2 as a retry of that ID. The FAIL count starts at 0: it counts only failures seen inside this run |
| Exactly one `in progress` row with no `## Corrections`. The tree is clean, or dirty only with that item's work | Step 3 for that ID, as a **recovery checkpoint** (below). Its run was abandoned mid-item |
| The tree is dirty with anything else | Stop. `git autocommit` runs `git add -A`, which would sweep unrelated edits into an item's commit |

**Liveness check.** Run `~/.claude/bin/todo-agent-live <sp> <ID> <M*60>` for the
row's ID, and log its output lines with the entry decision. The helper scans the
subagent metadata of every session of this project, not only this one, for agents
whose description names the ID.

- Exit 2: an agent is unfinished and has written its transcript within
  `--stall-minutes`. It is live.
- Exit 0: no agent is live. None was found, all finished, or all went silent. A
  killed session never marks its agents finished, so silence is the only signal it
  leaves. The `STALL` row keeps a paged agent from being taken over.
- Exit 64, or the helper is missing → stop.

**Recovery checkpoint.** A run that ends mid-item leaves the row `in progress` with
no `## Corrections`. Usually the session hit its usage limit. On 2026-10-30 a run hit
its limit just after it dispatched an implementer. The agent's first request was
refused, and the next session's loop stopped on the row and wasted its run.
Recovering automatically means a run started after a limit reset picks up where the
last one died.

Log `RECOVER <ID>` and run Step 3. `/todo-checkpoint <ID>` judges whatever the
abandoned run left, whether that is nothing or a complete implementation. Step 4 then
decides as usual:

- **PASS or WARN**: the abandoned run had finished the work, and the checkpoint
  commits and retires it.
- **FAIL**: the checkpoint writes `## Corrections` naming what is missing, and the
  loop retries at Step 2. This FAIL **does not count** toward `--max-fails`. It judged
  the abandoned run, not an attempt made by this one. Counting it would leave the
  default budget of 2 with only one real attempt.

---

## Dispatching next and checkpoint

Every `/todo-next` and `/todo-checkpoint` this loop runs (cycle steps 2 and 3, which
the Entry point's retry, `done` and recovery rows also reach) is dispatched to a fresh
subagent, never run in this session. Inline Skill runs load `todo-next.md` (14,755
bytes) and `todo-checkpoint.md` (32,260 bytes), about 47KB of command text per item,
plus each item's diffs, review reports and adjudication. REFACTOR-LOOPCTX-01 fixed the
same growth in `/refactor-loop`, whose session reached about 126k tokens by phase 5 on
2026-11-09 and degraded late-run judgment. A fresh subagent per command keeps this
session to gates, result lines and checks.

**Accepted residual risk.** The dispatch has no watchdog, by the operator's choice on
2026-11-11, mirroring `/refactor-loop`. The command's own implementer and reviewer run
nested inside the dispatch, out of this session's sight, so one stuck on a permission
prompt is not detected: that is the 2026-10-21 failure. Preflight's permission-mode
refusal and the `cron-auto-mode-gate.py` hook are the remaining guards, which is why
the session must run in auto mode.

### Before each dispatch: freshness and snapshot

Run these immediately before every dispatch, including a FAIL retry and the recovery
checkpoint. Select's gate alone misses those entry points, and a checkpoint's
`## Corrections` can change the plan after Select checked it.

1. **Row.** "Row" prints exactly one line for `<ID>`. For `next` it reads `ready`, or
   `in progress` with a `## Corrections` heading in the plan (a retry from step 4 or
   the Entry point's Corrections row). For `checkpoint` it reads `done`, or
   `in progress` only as the Entry point's recovery checkpoint.
2. **Files.** `.local/todos/<ID>.spec.md` and `.local/todos/<ID>.plan.md` exist, and
   neither `.local/completed/<ID>.spec.md` nor `.local/completed/<ID>.plan.md` does.
   A stale archive must not satisfy a later retirement check.
3. **Loop safety.** `~/.claude/bin/plan-loop-check .local/todos/<ID>.plan.md` passes.
   On failure, stop quoting every `FAIL` line, as in Select.
4. **Snapshot.** Write "Status snapshot" to `<sp>/todo-status-base.txt` and require
   "Duplicate IDs" to print nothing. For a checkpoint, also write "Pre-dispatch HEAD"
   to `<sp>/todo-pre-head.txt`.

Missing or failed evidence stops; the loop never repairs the commands' bookkeeping to
make a check pass. The two snapshot files belong to this dispatch: they survive an
asynchronous wait and context compaction, and are never rewritten when its completion
arrives.

### Dispatch

Use the Agent tool with `subagent_type: general-purpose` and `model: opus`, in the
foreground. Never use the `fork` subagent type, and never run either command with the
Skill tool in this session. The `description` names the ID with spaces around it,
`TODO <ID> — loop next` or `TODO <ID> — loop checkpoint`, so the Entry point's
`todo-agent-live` check finds a dispatch an earlier session left running. Pass the
matching prompt, verbatim except the placeholders.

For `/todo-next`:

```text
Invoke the Skill tool with skill "todo-next" and args "<ID>", and follow that command to its end in this repository.
- You run inside /todo-loop with no operator. Never ask a question; if the command would need an answer, stop and report it in the result line.
- The command spawns its own subagents (implementer, reviewer). If you cannot spawn one, stop and report it. Never implement or review inline yourself.
- Do not run git add, git commit, git autocommit, git push, git reset, git checkout, git clean, or any git stash form except the exact `git stash create` the command itself requires, and do not touch any live service.
- Ignore the command's closing advice to the operator (which command to run next). Do not act on it.
- Return at most ten summary lines, including blockers; omit raw diffs and review reports.
- Distinguish a legitimate no-change review skip from a missing required spawn. Only the latter stops. Emit outcome=done only after the entire command, including its review/adjudication and bookkeeping, has finished.
- End your reply with exactly one line in this grammar, as the last line:
  LOOP-RESULT next id=<ID> outcome=<done|blocked|stop>
  LOOP-RESULT stop reason=<one line>
```

For `/todo-checkpoint`:

```text
Invoke the Skill tool with skill "todo-checkpoint" and args "<ID>", and follow that command to its end in this repository.
- You run inside /todo-loop with no operator. Never ask a question; if the command would need an answer, stop and report it in the result line.
- The command spawns its own reviewer. If you cannot spawn it, stop and report it. Never review inline yourself.
- Run `git autocommit` only where the command's own commit step instructs it. Run no other git write: no git add, git commit, git push, git reset, git checkout, git clean, and no git stash form except the exact `git stash create` the command requires. If the commit fails or its guard skips it, do not retry and do not follow the advice to run it by hand; report it in the result line.
- Ignore the command's closing advice to the operator (which command to run next). Do not act on it.
- Return at most ten summary lines, including any TODO IDs the review tracked and any next-item status changes; omit raw diffs and review reports.
- A legitimate skip of an unchanged delta's reviewer is allowed. A missing required reviewer stops. Emit the checkpoint result only after commit handling and fix-ahead finish, never immediately upon retirement.
- End your reply with exactly one line in this grammar, as the last line:
  LOOP-RESULT checkpoint id=<ID> overall=<PASS|WARN|FAIL> commit=<sha|nothing|skipped|failed|n/a> demoted=<ID[,ID...]|none>
  LOOP-RESULT stop reason=<one line>
```

The commit rule differs from `/refactor-loop` on purpose. There the orchestrator
commits, so its prompt bans `git autocommit`. Here `/todo-checkpoint` commits on PASS
or WARN as its own file instructs, so its prompt permits exactly that commit; banning
it would leave every retired item uncommitted and the next item building on a dirty
tree.

`commit=` maps one-to-one onto `todo-checkpoint.md`'s Commit row: `<sha>` for a SHA,
`nothing` for `NOTHING TO COMMIT`, `skipped` for `SKIPPED`, `failed` for `FAILED`, and
`n/a` for FAIL, whose report has no Commit row. `demoted=` lists every item the
checkpoint's fix-ahead moved back to `planned` or `spec'd`: the next ready item and
each dependent citing the retired ID can all move. An `unattended: no` finding is not
a demotion. The subagent's summary and result line are the only command output this
session sees; no later step relies on either command's own text.

### A launch acknowledgement instead of a result

If the Agent call returns a launch acknowledgement rather than the subagent's reply,
log `WAIT <ID> <next|checkpoint> <launch id>` (the agent ID the acknowledgement names),
end the turn and start nothing else. The dispatch runs unwatched, as in
`/refactor-loop`: there is nothing to arm and nothing to stop later.

Resume on the completion notice for that launch. Bind it to the recorded launch ID,
target ID and role, not to whichever TODO ID was mentioned last: a nested agent's
completion inside the dispatch is not the dispatch result and never advances the
cycle. Handle a completion once. A duplicate or late notice for a launch already
handled is ignored, with no second mode check, `WARN`, verification or continuation.
After compaction, the log's `WAIT` line and the snapshot files from "Before each
dispatch" carry this state; use them, never a fresh snapshot.

### Completion mode check

After every dispatch returns, directly or by its completion notice, and before acting
on its result, run `~/.claude/bin/claude-permission-mode <sp>` (the real scratchpad
argument; never fall back to another session or guess a mode). The command's nested
implementer and reviewer now return inside the dispatch, out of this session's sight,
so a mode change mid-dispatch is caught only when the dispatch returns.

- `auto`, `bypassPermissions` or `dontAsk` → continue.
- `default`, `acceptEdits` or `plan` → stop with reason
  `permission mode <mode> at resume`, and tell the operator to restart the session in
  auto mode. The completed dispatch is never stopped.
- `unknown` → continue. Log an unknown-mode `WARN` only if this run has not yet
  logged one. Keep that fact in run state; after compaction, inspect records since
  the most recent `BEGIN` in `.local/TODO-LOOP.log`, not just a fixed-size tail.
  The preflight unknown `WARN` counts. Other `WARN` kinds and unknown warnings
  before this run's `BEGIN` do not consume its budget.
- Helper missing, not executable or failing, or any other value → stop, naming it.
  A failed lookup is not a pass.

A mode stop preserves the actual tracker status and tree. A completed implementer
may already have written `done`, and a partial attempt may remain `in progress`;
do not force either into the other, and do not roll back work. The Entry point
table resumes the item: `done` goes to checkpoint, and `in progress` goes through
its existing Corrections, liveness and recovery rules.

### After each dispatch: verify, then act

Parse the last non-empty line of the reply. It must match one of the `LOOP-RESULT`
forms exactly, and its form must be the dispatched command's (`next` or `checkpoint`)
or `stop`. A `next` or `checkpoint` line's `id` must equal the dispatched ID; the
`stop` form carries none. On a checkpoint line, `overall=FAIL` requires `commit=n/a`,
`overall=PASS|WARN` forbids it, and a `demoted=` list that names an ID twice is
malformed. A missing, unparseable or mismatched line stops, quoting it or the reply's
last paragraph.

Then check every field against disk and git before acting on it:

| Field | Check |
| --- | --- |
| `next … outcome=done` | "Row" reads `done`, and the spec and plan are still under `.local/todos/` |
| `next … outcome=blocked\|stop`, or `stop …` | None: stop, quoting the line and the summary |
| `overall=PASS\|WARN` | "Row" prints nothing, and "Completed files" lists both `.local/completed/<ID>.spec.md` and `.local/completed/<ID>.plan.md` |
| `overall=FAIL` | "Row" reads `in progress`, and "Corrections" finds a `## Corrections` heading in `.local/todos/<ID>.plan.md` |
| `commit=<sha>` | The claimed value is hexadecimal and "Claimed SHA" resolves it unambiguously to current HEAD; "HEAD parent" equals `<sp>/todo-pre-head.txt`; "Tree" prints nothing |
| `commit=nothing` | "Baseline" from the archived plan, `<sp>/todo-pre-head.txt` and current HEAD are all equal; "Tree" prints nothing |
| `commit=skipped\|failed` | None: step 4 stops on it |
| `commit=n/a` | Only with `overall=FAIL` (the parse rule above) |
| `demoted=` | Among IDs present in both `<sp>/todo-status-base.txt` and "Status now", those whose status is now `planned` or `spec'd` and differs from the snapshot equal the listed IDs exactly; `none` means that set is empty |

Any disagreement stops, and so does a "Duplicate IDs" line after the dispatch: never
collapse two rows into one status. A retired item simply disappears from "Status now"
and is not a demotion, and a `raw` row the review added is new rather than changed. A SHA that
does not resolve, resolves to an older commit, or whose parent is not the recorded
pre-dispatch HEAD cannot satisfy a commit claim, so an old commit never passes for a
new one.

PASS and WARN share the retirement check: `/todo-checkpoint` persists no verdict
beyond the retirement itself, so which of the two it was rests on the dispatch's
result line and summary, not on disk evidence. Log it as reported; never claim the
tracker proves it.

`<sp>` is the session scratchpad. Substitute every placeholder before running:

```bash
# Status snapshot (before every dispatch): one "ID|Status" line per row,
# keyed by ID so Order renumbering and summary edits never show as changes
awk -F'|' '/^\| [0-9]/ {gsub(/^ +| +$/, "", $4); gsub(/^ +| +$/, "", $5); print $4 "|" $5}' .local/TODO.md | sort > <sp>/todo-status-base.txt
# Duplicate IDs (before and after the dispatch; prints nothing when every ID is unique)
awk -F'|' '/^\| [0-9]/ {gsub(/^ +| +$/, "", $4); print $4}' .local/TODO.md | sort | uniq -d
# Pre-dispatch HEAD (before a checkpoint dispatch)
git rev-parse HEAD > <sp>/todo-pre-head.txt
# Status now (after the dispatch)
awk -F'|' '/^\| [0-9]/ {gsub(/^ +| +$/, "", $4); gsub(/^ +| +$/, "", $5); print $4 "|" $5}' .local/TODO.md | sort
# Row
grep -F '| <ID> |' .local/TODO.md
# Corrections
grep -n '^## Corrections' .local/todos/<ID>.plan.md
# Completed files
ls .local/completed/<ID>.spec.md .local/completed/<ID>.plan.md
# Baseline (archived plan)
grep -m 1 '^baseline:' .local/completed/<ID>.plan.md
# Claimed SHA
git rev-parse --verify --quiet '<sha>^{commit}'
# Last commit, tree, HEAD, HEAD parent
git log -1 --format='%h %s'
git status --porcelain
git rev-parse HEAD
git rev-parse HEAD^
```

The commands' own skip-review paths stay valid: an inability to spawn stops only when
a spawn was required, not when the command legitimately skips it.

---

## The cycle

1. **Select.** Re-read `.local/TODO.md`.
   - If this run has already retired `--max-items` items → stop: limit reached.
   - Take the eligible `ready` item with the smallest `Order`, using `/todo-next`'s
     own eligibility rules (dependencies satisfied, no external blocker).
   - None eligible → stop: queue drained. Name the lowest-Order item that is not
     `ready` and the preparation step it needs, such as `/todo-ready <id>`.
   - Its plan's `model:` is not `haiku`, `sonnet` or `opus` → stop: `/todo-next`
     would write a prompt file for an external model, which needs the operator.
     The queue is serial, so the loop does not skip past it.
   - `~/.claude/bin/plan-loop-check .local/todos/<ID>.plan.md` fails → stop, quoting
     every `FAIL` line. Do not repair the plan here: that is `/todo-plan`'s job, or
     the previous checkpoint's fix-ahead. The queue is serial, so the loop does not
     skip past it.

2. **Implement.** Log `START <ID> <model>`, or `RETRY <ID>` on a retry. Dispatch
   `/todo-next <ID>` as described in §Dispatching next and checkpoint, and verify its
   result line there.
   - `outcome=blocked`, a `stop` result, or any failed check → stop.
   - `outcome=done` continues only once "Row" reads `done`.

3. **Checkpoint.** Dispatch `/todo-checkpoint <ID>` the same way and verify its result
   line. Its verified `overall`, `commit` and `demoted` fields are all step 4 reads;
   the checkpoint's own report never reaches this session.

4. **Decide.** Act only on a result line that passed every check in §After each
   dispatch. First log one `DEMOTED <ID>` line for each ID in a verified `demoted=`
   list (none for `demoted=none`). Step 1 will not select a demoted item, and it needs
   the operator's `/todo-ready`. Log demotions before branching: the success branches
   below return straight to step 1, and logging placed after them would never run.
   - **`overall=PASS|WARN commit=<sha>`.** The checks proved the SHA is the new HEAD
     on top of the pre-dispatch HEAD and the tree is clean. Log the reported verdict
     with `git log -1 --format='%h %s'`, reset the FAIL count, count the item as
     retired, and go to step 1, which enforces `--max-items`.
   - **`overall=PASS|WARN commit=nothing`.** The checks proved the archived
     `baseline:`, the pre-dispatch HEAD and HEAD are equal and the tree is clean: the
     item genuinely changed nothing. Log that, reset the FAIL count, count the item
     as retired, and go to step 1. A moved HEAD, a dirty tree, or a missing or
     different archived `baseline:` (compare the SHA after the `baseline:` label that
     "Baseline" prints) has already stopped at the checks: something other than the
     checkpoint changed the repository, or the item's bookkeeping is wrong.
   - **`commit=skipped` or `commit=failed`** → stop, even though the checkpoint has
     already retired the item. It skipped fix-ahead, so the next item never runs on
     an uncommitted tree. Never re-dispatch the checkpoint for that absent row.
   - **`overall=FAIL commit=n/a`** → increment the FAIL count for `<ID>`, unless this
     was a recovery checkpoint (see Entry point). At `--max-fails` → stop. Otherwise
     go to step 2 as a retry. `/todo-next <ID>` picks up the `## Corrections` section
     the checkpoint wrote.
   - **Anything else**, including a missing or unparseable result line or a denied
     tool call → stop.

---

## Log

Append one line per event to `.local/TODO-LOOP.log`, using `date -Iseconds` for the
timestamp. The log is the loop's durable state. It survives context compaction and
is the first thing the operator reads, so on every resume read its tail before
acting.

```text
2026-10-21T00:21:08-04:00  BEGIN   mode=unknown max-items=- max-fails=2 stall=20m entry=step1
2026-10-21T00:21:09-04:00  WARN    permission mode unknown (no mode-bearing record); continuing
2026-10-21T00:21:12-04:00  START   FIX-TMPLBRACE-01  sonnet
2026-10-21T00:21:33-04:00  WAIT    FIX-TMPLBRACE-01  next  a7f3e91c
2026-10-21T07:23:40-04:00  PASS    FIX-TMPLBRACE-01  a1b2c3d  fix: stop substituting the brace-less $NAME form
2026-10-21T07:58:02-04:00  FAIL    FIX-TMPLSTRICT-01  1/2  C1, C2
2026-10-21T12:03:35-04:00  RECOVER FEAT-WAITRETRY-01  in progress, no Corrections; agent finished (usage limit)
2026-10-21T12:09:10-04:00  FAIL    FEAT-WAITRETRY-01  recovery (not counted)  C1
2026-10-21T08:30:47-04:00  STOP    queue drained; next: FIX-POLICYAMBIG-01 planned → /todo-ready
```

---

## Stop conditions

Stop on any of the following:

- `--max-items` reached, or the queue drained.
- `--max-fails` consecutive FAILs of one item.
- A failed commit, or a commit the log and git disagree on.
- An item whose model is external, or a `/todo-next` blocker.
- An item whose plan fails `plan-loop-check`.
- A preflight failure, or an entry-point state the table sends to stop.
- A prompting permission mode (`default`, `acceptEdits`, `plan`) when a dispatch
  returns (`permission mode <mode> at resume`), or a mode helper that is missing or
  failing there.
- A dispatch result line that is missing, malformed, names another ID or command,
  or disagrees with its disk or git check.
- A denied tool call.
- Any step that needs an action this file does not list.

Never improvise past a stop.

To stop:

1. Append a `STOP <reason>` line with enough evidence to act on: the item ID, the
   failing criterion, the denied command.
2. Leave the tree exactly as it is. Do not revert, stash, reset or clean anything,
   because the operator needs the evidence.
3. File every deferred item and open decision in `.local/TODO.md` with the
   `todo-add` skill.
4. Send `PushNotification` with one line, for example
   `todo-loop stopped: FIX-TMPLSTRICT-01 failed 2/2; 1 item committed`.
5. Report:

```text
═══════════════════════════════════════
 TODO loop
═══════════════════════════════════════
 Items retired this run   <ID — sha subject, one per line, or none>
 Last checkpoint          <ID> — PASS / WARN / FAIL
 Stop reason              <condition, with the evidence>
 Tree                     clean / dirty — <what is uncommitted>
 Queue                    <next eligible ready item, or the preparation step>
 TODO IDs filed           <ids, or none>
 Next                     <command for the operator>
═══════════════════════════════════════
```

---

## Scheduling

Before you leave:

1. Start the session in **auto** mode, with `claude --permission-mode auto` or
   Shift+Tab until the footer shows it. Do not use `acceptEdits`: it still prompts
   for shell commands outside the allowlist, which is what stalled 2026-10-21. The
   `cron-auto-mode-gate.py` PreToolUse hook enforces this by denying `CronCreate`
   in any other mode. It checks at scheduling time, and preflight re-checks when
   the job fires.
2. Run `/todo-loop --check` in that session and fix whatever it reports. Only
   `READY TO SCHEDULE` means the run is expected to finish unattended. On
   `NOT FULLY UNATTENDED`, either fix the named plans or schedule with the
   `--max-items` it gives.
3. Keep the machine awake (on macOS, leave `caffeinate -i` running in another
   terminal), and start Docker if the check says a queued item needs it.
4. Schedule a one-shot with `CronCreate`, `recurring: false`, with the cron pinned to
   the minute, hour, day and month (avoid :00 and :30), and this prompt:

   ```text
   Invoke the todo-loop skill with the Skill tool, args "--max-items <N>".
   ```

   The wording works whether or not a scheduled prompt expands slash commands.
   Confirm the actual next-run time with `CronList`.
5. Leave the session open and idle, and schedule nothing else in it (preflight stops
   on any other job). The job is session-only and fires only between turns.
6. With Remote Control connected, stop notifications reach your phone.
