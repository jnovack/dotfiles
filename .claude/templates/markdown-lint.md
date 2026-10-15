---
id: markdown-lint
scope: global
order: 28
---

## Markdown Lint Rules

All `.md` files must be lint-free, including pre-existing warnings in any file
you touch. A PostToolUse hook runs `markdownlint-cli2` on each `.md` you write
and reports what fails.

Do not lint or "fix" generated tracking files under `.local/` (`TODO.md`,
`REFACTOR*.md`, `REVIEW.md`, `ASSESSMENT.md`, `.local/completed/`). Their
repeated section templates trip MD024 by design, so fixing them breaks the
format and burns the turns meant for the actual work.

Rules most often missed:

- MD060: table pipes are spaced, `| --- | --- |`, not `|---|---|`.
- MD022/MD031/MD032: a blank line before and after every heading, code fence
  and list.
- MD040: every code fence declares a language (`text` if unknown). Use
  `csharp`, `cpp` and `fsharp`, not `c#`, `c++` or `f#`.
- Mermaid node labels use real indented line breaks, not `\n`.
