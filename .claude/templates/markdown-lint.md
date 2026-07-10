
<!-- markdown-lint.md -->
## Markdown Lint Rules

All `.md` files must be lint-free. Fix ALL warnings in any file touched, including
pre-existing ones.

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
