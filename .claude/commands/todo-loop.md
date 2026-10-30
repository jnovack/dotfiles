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
give. Nothing noticed. Three rules below exist because of that night: preflight
refuses a permission mode that prompts, every background agent gets a watchdog,
and every stall and stop sends a push notification.

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
- `--stall-minutes M` — transcript silence after which a background agent counts as
  stalled. Default `20`.
- `--check` — run Preflight only, print its result and the planned queue, and change
  nothing. Run it before scheduling, so a failing check surfaces while you are still
  at the keyboard rather than at 3am.

`<sp>` below is the session scratchpad directory from the system prompt. No
scratchpad listed → stop: both the mode check and the watchdog derive their paths
from it.

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
  to a live service, and never deploy.
- Never work around a failing test, a denied command, or a spec Constraint. Stop.
- Do not wrap this in `/loop` or schedule wakeups. Agent completion notices and
  watchdog exits resume the loop.

---

## Preflight

Run once, before the first cycle. Any failure is a stop (with `--check`, a report).

1. **Permission mode.** Run `~/.claude/bin/claude-permission-mode <sp>`.
   - `auto`, `bypassPermissions` or `dontAsk` → continue.
   - `default`, `acceptEdits` or `plan` → stop. Name the mode and tell the operator
     to restart the session in auto mode. These modes prompt for any command
     outside the allowlist, and an unattended prompt is a stall.
   - `unknown` (the transcript format changed) → log a `WARN` line and continue;
     the watchdog is the backstop.
   - Helper missing or not executable → stop.
2. **Helpers.** `~/.claude/bin/agent-watchdog` and `~/.claude/bin/plan-loop-check`
   exist and are executable.
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

| State at start | Begin at |
| --- | --- |
| No `done` or `in progress` row, and the tree is clean | Step 1 |
| Exactly one `done` row. The tree is clean, or dirty only with that item's work (files its plan's Steps or Placement name, their tests and docs) | Step 3 for that ID. Its implementer finished but was never checkpointed |
| Exactly one `in progress` row whose plan carries `## Corrections` | Step 2 as a retry of that ID. The FAIL count starts at 0: it counts only failures seen inside this run |
| An `in progress` row with no `## Corrections` | Stop. That item's agent may still be running, or it was abandoned. The operator runs `/todo-checkpoint <id>` by hand |
| More than one `done` or `in progress` row | Stop and list them |
| The tree is dirty with anything else | Stop. `git autocommit` runs `git add -A`, which would sweep unrelated edits into an item's commit |

---

## Waiting on background agents

`/todo-next` spawns an implementer and a reviewer, and `/todo-checkpoint` may spawn a
reviewer. When an Agent call returns a launch acknowledgement instead of a result,
the agent is running in the background. Every time that happens:

1. **Arm the watchdog** with `run_in_background`, and keep its task ID:

   ```bash
   ~/.claude/bin/agent-watchdog <sp>/../tasks/<agentId>.output <M*60>
   ```

   `<agentId>` comes from the launch result. The `tasks/` directory is the
   scratchpad's sibling, and it is the same path the completion notice names.
2. Append a `WAIT` line to the log, then end the turn. Start nothing else.
3. **Resume on whichever arrives first:**
   - **Agent completion notice.** `TaskStop` the watchdog, then continue the
     running skill exactly where its Agent call left off. For example, `/todo-next`
     continues at "After the subagent returns".
   - **Watchdog exit 0 (finished).** The completion notice is due or already
     handled. If it was handled, ignore the exit. Otherwise end the turn and wait
     for it.
   - **Watchdog exit 2 (stalled).** The agent has written nothing for `M` minutes,
     almost always because a permission prompt or an API error is waiting on a
     human. Append a `STALL` line and send `PushNotification`, for example
     `todo-loop: <ID> implementer silent 20m — likely a permission prompt`. Then end
     the turn without re-arming the watchdog. Do not stop the loop and do not
     touch the tree. The agent is still alive, and when the operator answers it,
     its completion notice resumes the loop. Send one notification per stall.
   - **Watchdog exit 64 or 66** (bad arguments, or no transcript). Log the exit,
     notify once, and keep waiting for the completion notice, unwatched.

An Agent call that returns its result directly needs no watchdog.

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

2. **Implement.** Log `START <ID> <model>`, or `RETRY <ID>` on a retry. Run
   `/todo-next <ID>` with the Skill tool and follow it to its end, including its own
   review and adjudication. Wait on its agents as described above.
   - If it stops without dispatching (a blocker, a missing spec or plan) → stop.
   - When it returns, the row must read `done`. Anything else → stop.

3. **Checkpoint.** Run `/todo-checkpoint <ID>` with the Skill tool, waiting on any
   reviewer it spawns. From its report, note the **Overall** result, the **Commit**
   row and the **Next-item plan** row.

4. **Decide.** The checkpoint report is a claim; check it against git.
   - **PASS or WARN, Commit shows a SHA.** `git log -1 --format='%h %s'` must match
     the reported SHA, and `git status --porcelain` must be empty. If either fails →
     stop. Otherwise log the result, reset the FAIL count, count the item as
     retired, and go to step 1.
   - **PASS or WARN, NOTHING TO COMMIT.** Read `baseline:` from
     `.local/completed/<ID>.plan.md`. If `git rev-parse HEAD` equals it, the item
     genuinely changed nothing: log that and go to step 1. Otherwise → stop.
     Something other than the checkpoint moved HEAD.
   - **Commit FAILED** → stop. The checkpoint has already skipped fix-ahead, so the
     next item never runs on an uncommitted tree.
   - **FAIL** → increment the FAIL count for `<ID>`. At `--max-fails` → stop.
     Otherwise go to step 2 as a retry. `/todo-next <ID>` picks up the
     `## Corrections` section the checkpoint wrote.
   - **Next-item plan moved an item back to `planned` or `spec'd`** → log a
     `DEMOTED` line. Step 1 will not select it, and it needs the operator's
     `/todo-ready`.
   - **Anything else**, including a missing report or a denied tool call → stop.

---

## Log

Append one line per event to `.local/TODO-LOOP.log`, using `date -Iseconds` for the
timestamp. The log is the loop's durable state. It survives context compaction and
is the first thing the operator reads, so on every resume read its tail before
acting.

```text
2026-10-21T00:21:08-04:00  BEGIN   mode=auto max-items=- max-fails=2 stall=20m entry=step1
2026-10-21T00:21:12-04:00  START   FIX-TMPLBRACE-01  sonnet
2026-10-21T00:21:33-04:00  WAIT    FIX-TMPLBRACE-01  implementer
2026-10-21T00:41:40-04:00  STALL   FIX-TMPLBRACE-01  implementer silent 20m
2026-10-21T07:23:40-04:00  PASS    FIX-TMPLBRACE-01  a1b2c3d  fix: stop substituting the brace-less $NAME form
2026-10-21T07:58:02-04:00  FAIL    FIX-TMPLSTRICT-01  1/2  C1, C2
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
- A denied tool call.
- Any step that needs an action this file does not list.

Never improvise past a stop. A stall is **not** a stop: the agent is still alive.

To stop:

1. Append a `STOP <reason>` line with enough evidence to act on: the item ID, the
   failing criterion, the denied command.
2. Leave the tree exactly as it is. Do not revert, stash, reset or clean anything,
   because the operator needs the evidence.
3. `TaskStop` any watchdog still running.
4. File every deferred item and open decision in `.local/TODO.md` with the
   `todo-add` skill.
5. Send `PushNotification` with one line, for example
   `todo-loop stopped: FIX-TMPLSTRICT-01 failed 2/2; 1 item committed`.
6. Report:

```text
═══════════════════════════════════════
 TODO loop
═══════════════════════════════════════
 Items retired this run   <ID — sha subject, one per line, or none>
 Last checkpoint          <ID> — PASS / WARN / FAIL
 Stalls                   <ID role minutes, or none>
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
6. With Remote Control connected, stall and stop notifications reach your phone, so
   a stall costs `--stall-minutes` instead of the night.
