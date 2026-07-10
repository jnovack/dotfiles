---
description: Execute the next eligible phase from .local/REFACTOR.md via a subagent at the phase's assigned model
---

# /refactor-next

Run the next incomplete phase in the refactor plan. One phase per invocation — do not chain.

---

## What to do

1. Read `.local/REFACTOR.md`.
2. In `## Phase Map`, find the first row where:
   - Status ≠ `Complete`, **and**
   - Every phase listed in "Depends on" has Status = `Complete` (or the field is `—`).
3. That is the **current phase**. Read its full section in `.local/REFACTOR.md`.
4. Check the `### Step Index` — if any rows are `In progress` or `Not started`, the phase is not done.
5. Note the phase's **Model** from the Phase Map row.
6. Construct the prompt and run by model — see below.

If no eligible phase exists (all complete, or all remaining are blocked by incomplete deps):
report the state and stop. Do not run anything.

---

## Prompt construction

Assemble three parts in order:

### Part 1 — Standard Preamble

Copy verbatim from the phase's `### Standard Preamble` section.

### Part 2 — Phase assignment

Copy verbatim: the phase header line, the **Files to modify** line, the `### Step Index`
table, and every `### Step N.x` section in order (full content, all code blocks).

### Part 3 — Closing instructions

Append exactly as written:

> You are executing a complete refactor phase. Work through each step in the Step Index
> in order. For each step, complete the implementation described in its section, then
> mark it `Complete` in the `### Step Index` table in `.local/REFACTOR.md`.
> After all steps are done:
>
> 1. Run the test command from `.local/REFACTOR.md` §Test Command.
>    Do not mark the phase complete if tests fail — report the failure and stop.
> 2. Mark the phase `Complete` in `## Phase Map` in `.local/REFACTOR.md`.
> 3. Append one row to `## Session Log`:
>    `| YYYY-MM-DD | Phase N — [name] | [model] | Complete | [one-line note] |`
>    Use `Partial` if any step was left incomplete, and explain why in the note.
> 4. Return a brief synopsis: what was done, any blockers or open questions, and
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

Codex cannot be auto-spawned. Write the full constructed prompt to `PROMPT.md` in the
project root for the user to paste into their Codex session. Then output:

```text
═══════════════════════════════════════
 Phase N — [name]
 Model: Codex
═══════════════════════════════════════

Prompt written to PROMPT.md. Paste it into your Codex session.

When Codex finishes:
- Confirm tests pass.
- Confirm Step Index and Phase Map are updated in .local/REFACTOR.md.
- Run /refactor-checkpoint to validate the Definition of Done.
═══════════════════════════════════════
```

Do not mark anything complete. Wait for the user to return.

---

## After the subagent returns (Haiku / Sonnet / Opus)

Report to the user:

1. Which phase ran and which model was used.
2. A 3–5 sentence synopsis of what was done.
3. Any blockers or open questions the subagent flagged.
4. The name and model of the next phase.

Then: **remind the user to run `/refactor-checkpoint` before advancing.**
Do not automatically invoke the next phase. Wait for `/refactor-next` to be called again.

---

## Error handling

- **Subagent fails or returns partial work**: leave affected steps `Not started`, report
  what went wrong, suggest retry or manual investigation.
- **Phase has no Step Index**: flag the inconsistency, do not run anything.
- **Dependency phases incomplete**: name which phases are blocking, stop.
- **All phases complete**: report done, state next action (PR, deploy, etc.).
