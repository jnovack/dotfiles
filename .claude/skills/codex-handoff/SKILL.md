---
name: codex-handoff
description: Hand a TODO or refactor phase to Codex for its boundary review — $todo-design-review after /todo-plan, $todo-closeout after /todo-checkpoint, $refactor-handoff before /refactor-next — run in a haiku subagent. Use whenever the user mentions Codex in the context of a TODO, a refactor phase or a handoff, for example "hand off to codex", "have codex prep it", "pass to codex", "let codex review it", "send it to codex", "codex closeout". Not for Codex requests unrelated to the todo or refactor workflow.
---

# Codex Handoff

The operator says "hand off to codex" instead of typing a `$skill` prompt. This
skill picks the Codex skill for the current boundary, builds its prompt, runs it
in a haiku subagent, verifies the result, and reports. It never commits.

## Step 1: Pick the boundary

Use the conversation first: the todo or refactor command run most recently, and
the item or phase it acted on. Confirm against disk. An explicit ID, refactor
name or skill in the request overrides the inference, but not the disk check.

| Boundary | Signal | Codex skill |
| --- | --- | --- |
| Prep a TODO | Item's row in `.local/TODO.md` is `planned` (just ran `/todo-plan`) | `$todo-design-review` |
| Close out a TODO | `/todo-checkpoint` passed: row gone, `.local/completed/<ID>.spec.md` and `.plan.md` exist | `$todo-closeout` |
| Refactor boundary | `.local/REFACTOR.md` row `planning`/`active`, next phase `Not started` (before `/refactor-next`) | `$refactor-handoff` |

- **Prep:** a `ready` row is reviewed again only if the user asks for it. A row
  that is `raw` or `spec'd` needs `/todo-plan` first: say so and stop. An
  `in progress` or `done` row is not a prep target.
- **Closeout:** a `done` row has not been checkpointed. Say `/todo-checkpoint`
  runs first, and stop. Closing out an unchecked item would review work that
  has not passed its Definition of Done.
- **Refactor:** read only the Phase Map
  (`sed -n '/^## Phase Map/,/^## /p' .local/REFACTOR.<kebab>.md`; the file is
  large). `PHASE` is the newest `Complete` phase and `NEXT_PHASE` the first
  `Not started` one. With no phase started, use `MODE=preflight` and pass only
  `NEXT_PHASE`. With every phase complete, use `MODE=final` and omit
  `NEXT_PHASE`. A retired refactor lives at
  `.local/completed/REFACTOR.<kebab>.completed.md`.

If more than one candidate fits and the conversation does not settle it, ask
one question naming the candidates. Do not guess: each Codex skill edits files.

## Step 2: Build the prompt

One line, shell-quoted. Every prompt ends with the shared suffix.

```text
Prep:     $todo-design-review TODO=<ID> (tracker .local/TODO.md, spec .local/todos/<ID>.spec.md, plan .local/todos/<ID>.plan.md). <noninteractive> <suffix>
Closeout: $todo-closeout TODO=<ID>. A passing /todo-checkpoint already retired it: the row was removed from .local/TODO.md and its spec and plan moved to .local/completed/<ID>.spec.md and .local/completed/<ID>.plan.md. That move is this repository's completion marker. <suffix>
Refactor: $refactor-handoff [MODE=preflight|final] [PHASE=<n>] [NEXT_PHASE=<n+1>] refactor=<kebab> (tracking file <path>). <suffix>
```

`<suffix>`: `Do not ask questions mid-run. Do not run git add, git commit or
git push, or anything against a live service.`

`<noninteractive>`, for prep only: `You run under codex exec and cannot
receive answers mid-run. Where Pass 1 needs a user decision, do not guess:
record it as an open question in the spec, leave the tracker status unchanged,
and end your final message with a numbered QUESTIONS: list, each giving your
recommendation and the alternatives.`

Why prep gets this: `$todo-design-review`'s Pass 1 is interactive, and under
`codex exec` nobody can answer. Without it Codex either stalls on a question or
invents the product decision the skill forbids it to invent.

## Step 3: Run it

Follow the global Running Codex rule: `codex exec` runs only inside a subagent.

1. `mktemp -d "<scratchpad>/codex.XXXXXX"` gives `<job>`, a fresh directory
   per run (`.local/` if the session lists no scratchpad; never `/tmp`).
2. Snapshot `git status --porcelain` and `git diff --stat`.
3. Dispatch the Agent tool, `subagent_type: general-purpose`, `model: haiku`,
   in the foreground, with this prompt (placeholders expanded):

   ```text
   Run one Codex job and report its result. Do not interpret or act on what Codex says.
   1. Verify <job> has no codex-exit.txt, codex-last.txt or codex-out.txt. If any exists, stop without launching. Load Monitor with ToolSearch query "select:Monitor"; if unavailable, stop.
   2. From <repo>, run this exact line with the Bash tool and run_in_background set to true:
      codex exec -s workspace-write -o <job>/codex-last.txt '<prompt>' > <job>/codex-out.txt 2>&1; echo $? > <job>/codex-exit.txt
   3. Use Monitor to wait until <job>/codex-exit.txt is nonempty (until test -s <job>/codex-exit.txt; do sleep 15; done). Do not end your turn before then, however long Codex runs. If the background command's completion notice arrives and the file is still empty or missing, stop waiting and report that the exit file was never written.
   4. Reply with: the contents of <job>/codex-exit.txt, the full contents of <job>/codex-last.txt, and every line of <job>/codex-out.txt that contains "ERROR:".
   ```

   This is the dispatch `/refactor-loop` uses (its §Running Codex). Keep the
   two in step: the Monitor wait exists because a haiku subagent was seen
   returning before Codex finished.

Wait for the subagent. Start no other work in the tree, since Codex is editing it.

## Step 4: Verify and report

The subagent's reply is a convenience; the job files are the evidence.

1. Run `~/.claude/bin/codex-job-status <job>`. `failed: …` → report it and stop.
   `unavailable: …` → Codex is out of usage: say so, and that nothing was
   reviewed. A missing exit file means Codex may still be live: report `<job>`
   and start nothing over it.
2. Read `<job>/codex-last.txt` yourself, and diff `git status --porcelain` and
   `git diff --stat` against the snapshot.
3. Check scope. Prep may change only the item's spec, plan and tracker row.
   Closeout may change only files tied to the item. Refactor may change only
   files that belong to `PHASE` plus the tracking file, and `NEXT_PHASE` must
   still be `Not started`. Report anything outside that as a finding. Do not
   revert it: the operator decides.
4. If Codex changed tracked files, update `.local/COMMIT-MSG.txt` so it
   describes the whole uncommitted set.
5. Report briefly: the boundary and Codex skill, Codex's findings and fixes,
   the files it changed, blockers, and the next command (`/todo-next`,
   `/refactor-next`, or nothing after a closeout).

## Step 5: Prep questions

When a prep run ends with a `QUESTIONS:` list, show the questions to the user,
with Codex's recommendation for each. Use AskUserQuestion when there are four
or fewer and each has a few distinct options; otherwise list them in text. Do
not answer them yourself.

With the answers, resume the same Codex session in a new `<job>` (Step 3, with
this line in place of the `codex exec` line):

```text
codex exec resume -c sandbox_mode="workspace-write" -o <job>/codex-last.txt <session-id> '<answers>. Continue the design review from where you stopped. <noninteractive> <suffix>' > <job>/codex-out.txt 2>&1; echo $? > <job>/codex-exit.txt
```

`<session-id>` is the UUID on the `session id:` line of the earlier job's
`codex-out.txt` header. `resume`
has no `-s` flag, so the sandbox is set through `-c`. Never use `--last`: it
picks the newest session in this directory, which may be a different run.
Repeat until Codex marks the item `ready` or reports a blocker.
