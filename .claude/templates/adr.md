<!-- adr.md -->
## Architecture Decision Records

ADRs live in `docs/decisions/`. They are the canonical record of *why* this
codebase is shaped the way it is. Treat them as load-bearing documentation.

### When to create an ADR

Create one when you have:

- Chosen between two or more viable technical approaches
- Introduced a new dependency
- Created a new module or significantly restructured an existing one
- Deviated from an existing pattern in the codebase
- Made a decision (including a refactor) whose reversal would require meaningful
  refactor effort

Do NOT create ADRs for: bug fixes, style choices, minor refactors, or
anything already covered by an existing record.

### When to read an ADR

Read reactively, not eagerly:

- When entering a module that references one in its header (e.g. `adr#NNNN-<kebab-title>.md`)
- Before making a decision that meets the trigger criteria above
- Never pre-load the full ADR corpus — check the index, pull only what's relevant

### When to amend an ADR

- Status changes only (Accepted → Superseded) when a new ADR replaces it
- Never rewrite history — append a note, don't edit past reasoning
- A superseded ADR must reference its successor

### Format rules

- Be a journalist — record what happened, not the ideal version
- No editorializing in favor of the chosen path
- Alternatives Considered must be honest about why they lost
- Consequences must include what was sacrificed, not just what was gained
- Hard 300 word limit per ADR — if you need more, your decision scope is too wide

### ADR creation is post-execution only

**Do not create or propose an ADR during planning or mid-task.**
ADRs record decisions that were made and executed, not intentions.
Run `/adr` after a plan has been fully executed.

### Index maintenance

`docs/decisions/README.md` must stay current.
Every ADR gets one line: `| NNNN | title | one-line summary | date | status |`
