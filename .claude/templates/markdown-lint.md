---
id: markdown-lint
scope: global
order: 28
---

## Markdown Lint Rules

All `.md` files must be lint-free. Fix ALL warnings in any file touched, including
pre-existing ones.

**Exception — generated tracking files under `.local/`.** These are gitignored
working files (`TODO.md`, `REFACTOR.md`, `REFACTOR.*.md`, `REVIEW.md`,
`ASSESSMENT.md`, and their archived copies under `.local/completed/`), machine-
maintained by the `/refactor-*`, `/todo-*` and `/review-*` command families. They are
built from repeated section templates, so MD024/no-duplicate-heading fires once per
phase or item **by construction** and can never be resolved without abandoning the
format. Do not lint them and do not "fix" their headings. Seen 2026-08-24: a phase
agent ran markdownlint on a `.local/REFACTOR.<kebab>.md` it had just edited, spent its
final turn adjudicating 24 structural MD024 warnings, and terminated before writing its
Session Log row and commit handoff. The rule below is for documentation you ship, not
for scratch state a command owns.

### Commonly missed rules

**MD060/table-column-style** — Table pipe spacing must be `| --- | --- |`, not `|---|---|`.

**MD022/blanks-around-headings** — Blank line required before and after every heading.

**MD031/blanks-around-fences** — Blank line required before and after every fenced
code block.

**MD032/blanks-around-lists** — Blank line required before and after every list.

**MD040/fenced-code-language** — Every fenced code block must declare a language
(use `text` if unknown):

````markdown
```mermaid
```bash
```text
````

Some language names contain characters that break renderers — use the safe identifier:

| Language | Use | Not |
| --- | --- | --- |
| C# | `csharp` | `c#` |
| C++ | `cpp` | `c++` |
| F# | `fsharp` | `f#` |

### Mermaid diagrams

Do not use `\n` inside node labels. Use actual line breaks with indentation:

```mermaid
graph LR
    Dev[Developer
        pushes code] --> GH[GitHub]
    GH --> Pipeline[GitHub Actions
        build + test]
```
