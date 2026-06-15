Review the entire repository and produce a file named REVIEW.md in `.local/REVIEW.md`.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist,
create it with the following content so these output files are never committed:

```text
*
!.gitignore
```

## Scope

Analyze all source files for:

- **Bugs** — logic errors, off-by-one errors, null/undefined dereferences, incorrect error handling, race conditions, improper resource cleanup
- **Security vulnerabilities** — injection risks (SQL, command, XSS), insecure defaults, hardcoded secrets or credentials, improper input validation, exposed sensitive data, insecure dependencies
- **Inconsistencies** — deviations from the conventions already established in this codebase (naming, error handling style, module patterns, etc.)
- **Best / leading practice violations** — only flag issues rooted in well-established patterns for the language and framework in use; do not invent standards

## Ground Rules

- Prefer the smallest correct change. Do not rewrite what works.
- Preserve existing structure, naming, and patterns unless they are the direct cause of a defect.
- Do not perform unrelated refactors, formatting passes, style normalization, or file moves.
- Any suggested new behavior must be backward-compatible and default-off (feature flag, opt-in config, etc.).
- Do not disagree for novelty's sake. Every finding must cite a specific, demonstrable problem.
- If a file has no meaningful issues, omit it from the report entirely.

## Additional Instructions

- Read every file before writing REVIEW.md. Do not emit partial results.
- Line numbers must be exact. Verify them against the actual file content before writing.
- Code blocks in Fix sections must be complete, runnable replacements — not pseudocode, not "something like this."
- If a suggested fix requires changes in more than one location, list all locations with their respective fix blocks.
- Do not add encouraging commentary, filler phrases, or meta-notes inside REVIEW.md. Keep it dense and actionable.
- Each finding must include a unique identifier using the format `#<MODULE>-<TYPE>-<N>`:
  - **MODULE**: 2–4 char uppercase abbreviation of the filename or module (e.g., AUTH, DB, API, UI, CFG)
  - **TYPE**: 2–4 char uppercase abbreviation of the issue class (e.g., NULL, INJ, RACE, LEAK, VAL, SEC, ERR)
  - **N**: 1-based integer scoped per file, resetting for each new file
  - Format heading as: `#### 🔴 Critical — #AUTH-NULL-1 — <short title>`
- Populate the Finding Index table at the top of REVIEW.md with every finding ID before writing per-file sections.
- For any finding involving legacy, deprecated, compatibility, or parallel-path code: before recommending a comment fix, grep production callers. Categorize results as: (a) production callers, (b) test-only callers, (c) zero callers. If (b) or (c), recommend deletion over documentation. If (a), document why the legacy path exists and what replaces it.

## REVIEW.md Format

Produce REVIEW.md with the following structure:

---

# Code Review

> Generated: <datetime in localtime>
> Reviewer: Claude Code
> Scope: Full repository

## Summary

A 3–5 sentence executive summary of the dominant issue patterns, and highest-priority concerns.

---

## Finding Index

A master table of all findings, emitted before the per-file sections:

| ID | Severity | File | Title |
| --- | --- | --- | --- |
| #AUTH-NULL-1 | 🔴 Critical | `auth/login.js` | Null dereference on missing user |
| #DB-INJ-1 | 🟠 High | `db/query.js` | Unsanitized input in raw query |

---

## Findings by File

Repeat the following block for each file that has findings, ordered by the highest severity issue present in that file (Critical first):

### `path/to/file.ext`

#### 🔴 Critical — #AUTH-NULL-1 — <short title>

**Line(s):** 42
**Issue:** Precise description of what is wrong and why it is dangerous or incorrect.
**Fix:**
\```language
// exact replacement code here
\```
**Rationale:** One sentence citing the pattern or standard this violates.

---

#### 🟠 High — #DB-INJ-1 — <short title>

**Line(s):** 87–91
**Issue:** ...
**Fix:** ...
**Rationale:** ...

---

#### 🟡 Medium — #API-VAL-1 — <short title>
**Line(s):** 120
**Issue:** ...
**Fix:** ...
**Rationale:** ...

---

#### 🔵 Low — #UI-ERR-1 — <short title>
**Line(s):** 205
**Issue:** ...
**Fix:** ...
**Rationale:** ...

---

## Severity Reference

| Level | Meaning |
|---|---|
| 🔴 Critical | Exploitable vulnerability, data loss risk, or crash in normal usage |
| 🟠 High | Likely bug or significant security weakness; fix before shipping |
| 🟡 Medium | Inconsistency or practice violation that will cause problems at scale |
| 🔵 Low | Minor refinement; fix when you're already touching the file |

---

## Quick Wins

A bulleted list of the 3–5 highest-leverage changes across the entire repo — things that fix the most risk for the least effort.
