---
description: Show the current state of the active refactor plan (read-only)
model: haiku
allowed-tools: Read
---

# /refactor-status

Report the current state of the active refactor plan. Read-only — nothing is run or
changed. Runs on Haiku via the `model` frontmatter.

---

## What to do

Read `.local/REFACTOR.md`. Extract:

1. `## Phase Map` — all rows (phase number, title, status, depends-on, model).
2. For every phase with Status ≠ `Not started`: read its `### Step Index` table.
3. `## Session Log` — the last 3 rows only.

Do not read step sections, code blocks, or preambles — the tables are enough.

---

## Output format

Print this report shape exactly. Use ✓ complete, → in progress, · not started, ✗ blocked:

```text
═══════════════════════════════════════
 Refactor — [Title from REFACTOR.md]
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
 Run:         /refactor-next
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
- If every phase is complete, say so clearly and state the next action.
- If nothing has started, output: `Ready to begin — run /refactor-next for Phase 1 ([model]).`
