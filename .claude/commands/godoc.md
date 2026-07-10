---
description: Add comprehensive GoDoc documentation to every Go symbol and package (documentation only, no behavior changes)
argument-hint: [path]
---

Review every Go source file in the project and add comprehensive GoDoc-compliant
documentation throughout. If a path argument is provided, restrict to packages
under that path; otherwise cover the full project.

Process one package at a time: document it completely, then run
`go vet ./<package>/...` before moving to the next — do not defer all
verification to one giant final pass.

For each package:

1. Right-size the package comment per the GoDoc tier rules in
   `templates/lang-golang.md` §Documentation (GoDoc):
   - **Contract packages** (imported by ≥2 other packages AND carrying a contract the
     source alone does not show — lifecycle ordering, concurrency guarantees, wire/data
     formats, extension points) get a full doc.go: purpose, contract, non-obvious
     design decisions.
   - **Every other package** gets a brief package comment, ≤10 lines: what it provides
     and who consumes it.
   - This cuts both ways: SHRINK an existing doc.go that exceeds its tier.
   - Never include file-layout listings, "why this is a separate package" rationale,
     or prose restating code structure — these go stale silently.
   - When several packages implement one shared pattern, document the pattern once in
     the contract package; implementations document only their deltas.

2. Document every exported AND unexported type, function, method, var, and const that
   lacks a comment. For each:
   - Lead the comment with the symbol name
   - Describe what it is, what it does, and why it exists
   - Note parameter semantics, return values, error conditions, and fallback behaviour
   - Call out invariants, ordering guarantees, or concurrency safety where relevant

3. For files with multiple logical groups of declarations, add section header comments
   using the ─── Section Name ─── style to make the file scannable at a glance.

4. Do NOT change any behaviour. Documentation only — no refactoring, no renaming,
   no new code.

After all packages are done: `go vet ./...` (or scoped to the path argument)
must pass with zero errors.
