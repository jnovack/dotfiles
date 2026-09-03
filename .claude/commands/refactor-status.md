---
description: Show the current state of the refactor index, or one refactor's phases (read-only)
argument-hint: [<refactor>]
model: haiku
allowed-tools: Read
---

# /refactor-status

Report refactor state. Read-only — nothing is run or changed. Runs on Haiku via the
`model` frontmatter.

- **No argument** — a dashboard of every refactor in the `.local/REFACTOR.md` index.
- **A kebab title** — the phase-by-phase view of that one refactor's
  `.local/REFACTOR.<kebab>.md`.

---

## No argument — index dashboard

Read `.local/REFACTOR.md`. If it does not exist, or its table has no rows, output:

```text
No active refactors — run /refactor-init to start one.
```

Otherwise, for each row read `## Phase Map` from that refactor's
`.local/REFACTOR.<kebab>.md` (Phase Map only — not step sections or preambles) and print:

```text
═══════════════════════════════════════
 Refactors
═══════════════════════════════════════

 <kebab>                     [STATUS]   <done>/<total> phases
   next: Phase <N> — <name>  (<model>)
   last: <date> — Phase <N> — <Complete|Checkpoint failed>

 <kebab>                     [STATUS]   <done>/<total> phases
   ...
───────────────────────────────────────
 Run:  /refactor-next <kebab>      (or with no arg if only one is active)
═══════════════════════════════════════
```

- `STATUS` is the index Status verbatim (`planning` / `active` / `blocked`).
- `next` is the first Phase Map row that is not `Complete` and whose deps are all
  `Complete`; omit the line if every phase is done (shouldn't happen — a finished
  refactor is retired out of the index).
- `last` is the most recent `## Session Log` row; omit if the log is empty.

If `.local/REFACTOR.md` contains `## Phase Map` or `## Intent` (old single-file
format), say so and tell the user to rename it to `.local/REFACTOR.<kebab>.md` and
create an index.

---

## With a kebab title — one refactor's phases

Read `.local/REFACTOR.<kebab>.md`. Extract:

1. `## Phase Map` — all rows (phase number, title, status, depends-on, model).
2. For every phase with Status ≠ `Not started`: read its `### Step Index` table.
3. `## Session Log` — the last 3 rows only.

Do not read step sections, code blocks, or preambles — the tables are enough.

Print this report shape exactly. Use ✓ complete, → in progress, · not started, ✗ blocked:

```text
═══════════════════════════════════════
 Refactor — [Title from REFACTOR.<kebab>.md]
═══════════════════════════════════════

Phase 1 — [name]                        [STATUS]
  ✓/→/· 1.a  [step description]         [model]
  ✓/→/· 1.b  [step description]         [model]
  ✗ 1.c  [step description]             [model]  ← blocked: [what]

Phase 2 — [name]                        [NOT STARTED — waiting on Phase 1]
  (steps not shown until phase begins)

Phase 3 — [name]                        [NOT STARTED — waiting on Phase 2]
  (steps not shown until phase begins)

───────────────────────────────────────
 Next phase:  [N] — [name]
 Model:       [model]
 Run:         /refactor-next [<kebab>]
───────────────────────────────────────
 Last session: [date] — Phase [N] — [name] — [Complete/Partial]
               [date] — Phase [N] — [name] — [Complete/Partial]
═══════════════════════════════════════
```

Rules:

- The model shown on step rows is the phase's model repeated — steps do not
  have individual model assignments; do not hunt for a per-step model field.
- Show all step rows for any phase that has at least one step started.
- For phases not yet started, collapse to one line noting what they depend on.
- If a phase's deps are incomplete, mark it ✗ and state what is blocking it.
- Show the last 3 session log rows if they exist; omit the section if the log is empty.
- If every phase is complete, say so clearly — the refactor is ready for its final
  `/refactor-checkpoint <kebab>`, which retires it.
- If nothing has started, output: `Ready to begin — run /refactor-next <kebab> for Phase 1 ([model]).`
