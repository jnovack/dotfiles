# Assessment

Review the entire repository and produce a file named ASSESSMENT.md in `.local/ASSESSMENT.md`.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist,
create it with the following content so these output files are never committed:

```text
*
!.gitignore
```

## Purpose

This assessment evaluates code for human comprehensibility — not correctness, not performance, not security. The code may have been written by an agent, a human, or a blender. The question is: can a human engineer understand, maintain, and reason about it without reverse-engineering intent from behavior?

## Scope

Analyze all source files for:

- **Missing or inadequate documentation** — undocumented modules, exported functions, or public interfaces where the *why* and *what* are not apparent from the signature alone
- **Missing inline reasoning** — mid-function workarounds, non-obvious conditionals, magic values, or control flow that required thought to write but has no comment explaining *why it exists*; do not flag self-evident code
- **Inconsistent application of patterns** — a fix, guard, normalization, or convention applied in one location but missing from analogous locations that share the same risk or role; flag the gap, not just the original
- **Structural confusion** — logic split across locations in a way that obscures the full picture; responsibilities that bleed across modules in ways that will mislead the next reader; temporal ordering that made sense during development but not during maintenance
- **Naming that lies or misleads** — names that contradict behavior, overpromise scope, or require reading the implementation to decode; names that differ across call sites for the same concept
- **Dead or vestigial code** — commented-out blocks left in, imports never used, flags never checked, code paths that cannot be reached; flag only what a reader would waste time trying to understand
- **Implicit contracts** — assumptions about input shape, call order, shared state, or external conditions that are nowhere stated and not obvious; anything a caller must know that isn't captured in the interface
- **Overengineering** - Review diffs for unnecessary complexity. Stop at the first rung that holds. The ladder is a reflex, not a research project. Two rungs work → take the higher one and move on. The first lazy solution that works is the right one.

  1. Does this need to exist at all? Speculative need = skip it, say so in one line. (YAGNI)
  2. Stdlib does it? Use it.
  3. Native platform feature covers it? `<input type="date">` over a picker lib, CSS over JS, DB constraint over app code.
  4. Already-installed dependency solves it? Use it. Never add a new one for what a few lines can do.
  5. Can it be one line? One line.
  6. Only then: the minimum code that works.

## Ground Rules

- **Do not conflate this with a bug review.** If a finding is purely a correctness issue, omit it. This command is about comprehensibility.
- **Omit self-evident code.** `i++` does not need a comment. Flag absence of documentation only where a reader would genuinely pause.
- **Prefer the smallest correct change.** A one-line comment often fixes a finding. Don't suggest a refactor when a comment will do.
- **Preserve existing structure.** Do not recommend restructuring that isn't directly necessary to make code understandable.
- **Flag inconsistency at the gap, not just the origin.** If function A has a guard that B and C lack, the finding is on B and C.
- **Every finding must cite a specific, demonstrable problem.** "Could be clearer" is not a finding. "Caller has no way to know this mutates the input" is.
- **If a file has no meaningful issues, omit it from the report entirely.**

## Additional Instructions

- Read every file before writing ASSESSMENT.md. Do not emit partial results. Where a code graph or symbol index is available, use it to identify call sites, analogous functions, and module boundaries before doing full file reads — this reduces redundant token use without sacrificing coverage.
- Line numbers must be exact. Verify them against the actual file content.
- Fix blocks must be complete and runnable — no pseudocode, no "add a comment here," no ellipsis standing in for real code.
- If a fix requires changes in more than one location, list all locations with their respective fix blocks.
- Do not add encouraging commentary, filler phrases, or meta-notes. Keep it dense and actionable.
- Do not re-explain the finding inside the fix block. The fix should speak for itself.
- For any finding involving legacy, deprecated, compatibility, or parallel-path code: before recommending a comment fix, grep production callers. Categorize results as: (a) production callers, (b) test-only callers, (c) zero callers. If (b) or (c), recommend deletion over documentation. If (a), document why the legacy path exists and what replaces it.

---

## Output Format

### Finding Index

Populate this table before writing per-file sections. Every finding must appear here.

| ID | Severity | File | Title |
| --- | -------- | ---- | ----- |
| #AUTH-DOC-01 | 🟡 Warning | auth.js | `verifyToken` has no documented failure modes |

---

### Per-File Findings

Group findings by file. Within each file, order by line number.

#### Finding Format

```text
#### 🔴 Critical — #<MODULE>-<TYPE>-<NN> — <short title>

**Lines:** <exact line number(s)>
**Problem:** <what a reader will misunderstand, miss, or have to reverse-engineer>
**Fix:**

    ```<language>
    <complete, runnable replacement — no pseudocode, no ellipsis>
    ```
```

#### Severity Levels

- 🔴 **Critical** — A reader will almost certainly misunderstand this and introduce a defect or make a wrong assumption during maintenance
- 🟡 **Warning** — A reader will need to slow down, cross-reference, or guess; ongoing maintenance risk
- 🔵 **Note** — Minor gap; low immediate risk but degrades the codebase over time

#### Finding Type Codes

| Type | Meaning |
| --- | --- |
| DOC | Missing or misleading module/function/class documentation |
| WHY | Missing inline rationale for a non-obvious decision, workaround, or magic value |
| GAP | Pattern or guard present in one place but absent from analogous locations |
| NAME | Name contradicts or obscures behavior |
| DEAD | Unreachable, unused, or vestigial code a reader will waste time on |
| CNTR | Implicit contract — assumption about inputs, call order, or state not captured at the interface |
| STRCT | Structural confusion — logic split or bled across locations in a misleading way |

#### ID Format

`#<MODULE>-<TYPE>-<NN>`

- **MODULE**: 2–4 char uppercase abbreviation of the filename (e.g., AUTH, DB, API, UI, CFG)
- **TYPE**: from table above
- **NN**: 2-digit left-zero-padded integer, incrementing globally across the entire report (never resets per file); e.g., `01`, `02`, … `10`, `11`

Example heading: `#### 🟡 Warning — #DB-GAP-07 — Connection error handler missing in \`queryBatch\``
