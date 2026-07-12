---
description: Review source files for bugs, security, and reliability issues; write findings to .local/REVIEW.md
argument-hint: [path]
---

Review the repository and produce `.local/REVIEW.md`.

If a path argument is provided (e.g. `/review src/` or `/review cmd/app1`), restrict
all file discovery and analysis to that path. Otherwise review the full repository.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist,
create it with:

```text
*
!.gitignore
```

---

## Pre-Analysis Phase

If the `code-review-graph` MCP tools are available, use them first
(`get_architecture_overview`, `semantic_search_nodes`, `query_graph`) to map call
sites, analogous functions, and module boundaries before full file reads — this
reduces redundant token use without sacrificing coverage. For large repositories,
prefer scoping with a path argument, or use `/review-comprehensive`, whose parallel
agents each get a fresh context.

Read every source file in scope. Then, before writing any finding, work through the
checklist below for EACH file in order. Do not skip files or checklist items. Keep
private notes as needed, but do not write `REVIEW.md` until the checklist has been
completed for all files.

Only record a finding if it is supported by concrete code evidence and represents a
real bug, security risk, reliability issue, or meaningful maintainability problem. Do
not report speculative issues, stylistic preferences, or risks already handled
elsewhere in the codebase.

For each finding, identify: file and line number; severity (Critical, High, Medium,
or Low); the specific failure mode; why the current code permits it; a minimal
suggested fix; and any test that should be added or changed.

<!-- Keep this checklist in sync with the DIMENSIONS prompts in
review-comprehensive.md and the summary in ../docs/README.review-commands.md -->

**Checklist for each file:**

1. **Absent-value safety** — every value that could be null, nil, None, undefined,
   empty, zero-value-invalid, or a typed null: is it checked before use?

2. **Error/exception propagation** — every operation that can fail: is the error
   checked? Does propagation preserve cause/context? Is nothing silently swallowed
   or replaced with a misleading message?

3. **Resource lifecycle** — every file handle, connection, lock, socket, goroutine,
   thread, timer, ticker, request body, response body, or allocated resource: is
   there a guaranteed release on all exit paths, including error paths?

4. **Concurrency** — every value accessed from multiple goroutines/threads/tasks: is
   it synchronized or immutable? Every async operation: is its lifetime bounded,
   cancellable where appropriate, and failure observable?

5. **Trust boundary validation** — every value arriving from outside this module,
   including user input, env vars, config files, external APIs, CLI args, HTTP
   headers, serialized data, and filesystem state: is it validated or sanitized
   before use?

6. **Credential/secret exposure** — can any variable, field, error message, panic,
   response, metric, trace, or log line leak a secret, key, token, credential,
   or PII?

7. **Injection surfaces** — every place external data is composed into a query, shell
   command, template, URL, HTTP header, regex, file path, archive path, or code
   expression: is it escaped, parameterized, allowlisted, or otherwise safe?

8. **Test completeness** — for each tested function or behavior: are negative cases
   present? Boundary conditions? Error paths? Do tests rely on timing assumptions,
   global state mutation, ordering, network access, local machine state, or
   implementation details? This is a spot-check only — use `/review-tests` for a
   comprehensive test-layer audit.

9. **Convention consistency** — does this file follow the naming, error-handling,
   logging, testing, and structural patterns already established in this codebase?

After completing the checklist for all files, write `REVIEW.md`. If there are no
findings, say so explicitly and note any areas where coverage was limited or residual
risk cannot be ruled out from static analysis alone.

---

## Ground Rules

- Prefer the smallest correct change. Do not rewrite what works.
- A minimal fix that contradicts a governing ADR or documented contract is not
  minimal — it is wrong. Before sizing a fix, check `docs/decisions/` (or the
  project's equivalent decision record) and the touched function/type's doc
  comment. If the smallest patch conflicts with either, report the
  architecturally-correct fix instead — even if it's larger — and say so
  explicitly (see `**Scope:**` in the finding format below).
- Cite what governing intent was checked for each finding, when one exists. A
  finding with no governing ADR should say "no governing ADR found" rather
  than imply the check was done and passed.
- Preserve existing structure, naming, and patterns unless they are the direct cause
  of a defect.
- Do not perform unrelated refactors, formatting passes, style normalization, or file
  moves.
- Every finding must cite a specific, demonstrable problem.
- If a file has no meaningful issues, omit it from the report.

---

## Output Instructions

- Line numbers must be exact — verify against the file before writing.
- For the `Generated:` timestamp, run `date` — do not guess the datetime.
- Fix code blocks must be complete, runnable replacements — not pseudocode.
- If a fix spans multiple locations, list all locations with separate fix blocks.
- No encouraging commentary or meta-notes. Keep findings dense and actionable.
- Each finding ID format: `#MODULE-TYPE-NN`
  - MODULE: 2–5 char uppercase file abbreviation (e.g. `AUTH`, `DB`, `MW`)
  - TYPE: 2–5 char uppercase issue class (e.g. `NULL`, `INJ`, `RACE`, `LEAK`, `SEC`)
  - NN: 2-digit 1-based integer, incrementing globally across the entire report
    (never resets per module-type pair), so every full ID is unique
- For legacy/deprecated/compatibility code: grep callers before recommending a fix.
  Categorize as (a) production callers, (b) test-only, or (c) zero callers.
  Recommend deletion if (b) or (c).
- Within each finding, add a `**Suggested Model/Effort:**` line in exactly this
  format — it is parsed by `/review-fix` and `/review-triage`:

  ```text
  **Suggested Model/Effort:** <Model> / <Effort> — <one sentence: blast radius or ambiguity>
  ```

  with Model in {Haiku, Sonnet, Opus, Codex} and Effort in {Low, Medium, High}.
  Size by blast radius and ambiguity, not severity. **Codex-first:** any
  zero-ambiguity, mechanical fix defaults to Codex/Medium — a Critical finding
  with an unambiguous one-line fix in a single file is still Codex/Medium.
  Assign Haiku/Low only when a Codex handoff is not viable for that specific
  finding. A finding whose fix contradicts a governing ADR or requires a
  product decision the report cannot make unilaterally is Opus/High regardless
  of diff size. Pick Model by how much reasoning correctness requires and
  Effort by how much verification trusting it requires, independently of each
  other.

---

## REVIEW.md Format

Produce REVIEW.md with the following structure:

### Header

```markdown
# Code Review

> Generated: [datetime in localtime]
> Reviewer: Claude Code
> Scope: [full repo, or scoped path]
```

### Summary section

3–5 sentence executive summary of dominant issue patterns and highest-priority
concerns.

### Finding Index

A master table of all findings emitted before the per-file sections:

| ID | Severity | File | Title |
| --- | --- | --- | --- |
| #AUTH-NULL-01 | 🔴 Critical | `auth/login.js` | Null dereference on missing user |
| #DB-INJ-01 | 🟠 High | `db/query.js` | Unsanitized input in raw query |

### Findings by File

One block per file that has findings, ordered by highest severity in that file.
Within each file, findings are ordered Critical → High → Medium → Low.

#### 🔴 Critical — #AUTH-NULL-01 — [short title]

**Line(s):** 42

**Issue:** Precise description of what is wrong and why it is dangerous or incorrect.

**Scope:** Only present when the correct fix is larger than the smallest patch that
would silence the symptom. One or two sentences: which ADR or documented contract
the minimal patch would violate, and why the larger fix is the actual smallest
*correct* change. Omit this line entirely when the minimal patch and the correct
patch are the same.

**Suggested Model/Effort:** `<Model> / <Effort> — <one sentence>` noting impact
radius, gotchas, or pitfalls (exact format above — parsed by `/review-fix`).

**Fix:**

```language
// exact replacement code here
```

**Rationale:** One sentence citing the pattern or standard this violates.

**Test:** One sentence describing the test to add or change, or "n/a" if already
covered by existing tests.

---

### Severity Reference

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Exploitable vulnerability, data loss risk, or crash in normal usage |
| 🟠 High | Likely bug or significant security weakness; fix before shipping |
| 🟡 Medium | Inconsistency or practice violation that will cause problems at scale |
| 🔵 Low | Minor refinement; fix when already touching the file |

### Quick Wins

A bulleted list of the 3–5 highest-leverage changes across the repo — things that
fix the most risk for the least effort.
