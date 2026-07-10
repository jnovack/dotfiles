---
description: Review code for human comprehensibility (docs, naming, implicit contracts, dead code); writes .local/ASSESSMENT.md
argument-hint: [path]
---

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
- **Overengineering** - Review code for unnecessary complexity. Stop at the first rung that holds. The ladder is a reflex, not a research project. Two rungs work → take the higher one and move on. The first lazy solution that works is the right one.

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
- **A comment is not a fix for code that violates a governing ADR or documented contract.** If the confusing code exists *because* it papers over or contradicts a decision record, say so in the finding instead of only recommending a comment — otherwise the fix documents duct tape rather than flagging it.
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
- Within each finding, add a line with the suggested model and effort (Haiku/Sonnet/Opus/Codex; Low/Medium/High) needed to correctly apply the fix. Size by blast radius and ambiguity, not by the finding's severity label — a Critical finding that's a one-line, unambiguous comment in a single file is still Haiku/Low; a Warning whose fix requires amending a governing ADR or a product decision the report cannot make unilaterally is Opus/High regardless of how small the resulting diff looks. See the sizing table below.

### Model/Effort sizing table

| Tier | Criteria |
| --- | --- |
| Haiku / Low | Pure comment/doc fix, one file, one location, zero behavior change, zero ambiguity in the fix's correctness. |
| Sonnet / Low | No behavior change, but the fix needs cross-file consistency, or correctness on a widely-used interface/type/contract, to get right. |
| Sonnet / Medium | Small structural cleanup (dedupe, hoist, delete dead code, extract a helper) contained to one package; needs a caller check and/or a test touch-up. |
| Sonnet / High | The correct fix is a real behavior change, not just wording — needs verification of an assumption and a test before landing. |
| Opus / Medium | Needs Opus-level reasoning to get right (e.g. an actual concurrency-safety argument, not a restated assumption) but does not need a human product decision — the agent can resolve it correctly on its own once it reasons carefully, it just can't be trusted to a lighter model. |
| Opus / High | Architecture/ADR-governance conflict, or a product decision the report cannot make unilaterally. Flag that a human checkpoint is needed before any code is written — do not let a fix pass silently pick a default. |
| Codex / Medium | Mechanical, low-judgment edit repeated across many locations or files, where diff precision matters more than reasoning — a strong batching candidate. |

This table is illustrative, not exhaustive — pick the model by how much
reasoning correctness requires and the effort by how much verification
trusting it requires, independently of each other, rather than forcing a
finding into the nearest listed combination.

Before assigning Opus/High to a finding whose fix is "just a comment": check
whether writing that comment requires asserting a rationale for a magic
number, formula, or derived value. If so, re-derive the value from the code
it describes rather than trusting the pattern of a nearby, already-explained
constant — two constants that look like siblings (e.g. a header width and
the rule that underlines it) can silently drift out of sync, and the
"undocumented magic number" you were asked to explain may actually be wrong,
not just unexplained. Say so in the Problem text if you find this; it changes
the finding from a doc gap to a real bug and should be sized accordingly.

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
**Suggested Model/Effort:** <Model> / <Effort> — <one sentence: blast radius, ambiguity, or why this tier>
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
