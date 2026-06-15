Review every Go source file in the project and add comprehensive GoDoc-compliant
documentation throughout. For each package:

1. Rewrite doc.go (or create one if absent) with a full package-level comment covering:
   architecture, file layout, request/data flow, and any non-obvious design decisions.

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

After all edits: go vet ./... must pass with zero errors.
