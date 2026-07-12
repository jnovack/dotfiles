# Claude Instruction Templating Machine

A single-source-of-truth system for the shared prose in `CLAUDE.md` /
`AGENTS.md` across every repo. Reusable instructions live once as templates;
an injector assembles them — resolving dependencies and deduplicating — into a
marked, hash-stamped region of each consuming file. A drift check keeps the
region honest.

Design rationale lives in
[`../PLAN.templating-machine.md`](../PLAN.templating-machine.md). This is the
operator guide.

## Why this exists

The same prose ("smallest correct change", "summarize what changed", the Go
testing philosophy) was copy-pasted across 30-plus instruction files and even
duplicated between templates. Edits never propagated; files silently diverged.
This machine makes duplication structurally impossible: prose has exactly one
home, and every file that uses it is regenerated from that home.

## Concepts

| Term | Meaning |
| --- | --- |
| Template | One reusable section of prose, in `.claude/templates/<id>.md` |
| Front-matter | Injector-only metadata (`id`, `scope`, `requires`, `order`) — stripped at assembly, never shown to the model |
| Scope | `global` (lives in `~/.claude/CLAUDE.md`, inherited by every repo) or `project` (opt-in per repo) |
| Recipe | The `<!-- templates: ... -->` line in a consuming file listing which templates it wants |
| Marked region | The `<!-- BEGIN/END TEMPLATES -->` block the injector owns and rewrites |
| Canonical file | The per-repo `CLAUDE.md` (the official file; `AGENTS.md` references it) |

Content **outside** the marked region is never touched — that is where
project-specific prose and deliberate overrides live.

## File layout

```text
~/Source/dotfiles/.claude/
  templates/<id>.md            <- source of truth for each prose fragment
  bin/claude-templates         <- the injector CLI
  docs/README.claude-templates.md   <- this guide

<repo>/
  CLAUDE.md                    <- canonical; contains a recipe + marked region
  AGENTS.md                    <- one line: "review CLAUDE.md"
```

## Anatomy of a template

Front-matter is YAML the injector reads and then discards. The body is the
prose that gets emitted.

```markdown
---
id: lang-golang
scope: project
requires: [testing-philosophy, command-hygiene]
order: 40
---

## go
...prose...
```

- `id` — stable name used in recipes and in other templates' `requires`.
- `scope` — `global` (lives in `~/.claude/CLAUDE.md`, inherited by every repo)
  or `project` (opt-in per repo). See "Global vs project scope" below.
- `requires` — templates this one assumes. The injector pulls them in
  automatically and emits each exactly once (the deduplication engine).
- `order` — canonical sort key so assembled files read consistently: core
  first, language last. Ties break by recipe position, then `id`.

## Anatomy of a consuming file

```text
# CLAUDE.md

(project identity — the parts unique to this repo)

<!-- templates: core-rules, response-expectations, lang-golang, markdown-lint -->
<!-- BEGIN TEMPLATES v:1 hash:<sha256> -->
(assembled, deduped, ordered prose — do not hand-edit)
<!-- END TEMPLATES -->

## Project overrides
(only where a template rule is intentionally not followed; state that it
supersedes the template point above)
```

You edit two things by hand: the identity prose above the block and the
`<!-- templates: -->` recipe. Everything between the markers is generated.

## Global vs project scope

Claude Code loads **both** `~/.claude/CLAUDE.md` and the repo's `CLAUDE.md`
every session. A template placed in both would appear twice in the loaded
context, so scope decides where each one lives and the injector dedups across
the two layers:

- **`scope: global`** templates live only in `~/.claude/CLAUDE.md` and are
  inherited by every repo. Do **not** list them in a project recipe.
- **`scope: project`** templates are opt-in per repo.
- When a project template `requires` a global one (e.g. `lang-golang` needs
  `testing-philosophy`), the injector treats it as already provided by the
  global layer and omits it from the project block. `check` warns if a project
  recipe names a global template directly.

| Global layer | Project layer |
| --- | --- |
| `core-rules`, `response-expectations` | `lang-golang` / `-dotnet` / `-nodejs` / `-swift` |
| `change-sizing`, `intent-capture` | `ansible`, `playwright`, `ui-defaults` |
| `documentation-style`, `testing-philosophy` | `adr`, `troubleshooting` |
| `markdown-lint`, `command-hygiene` | — |
| `commit-handoff`, `code-review-graph` | — |

## CLI reference

Run from the repo you want to affect (or pass a path).

| Command | Does |
| --- | --- |
| `claude-templates assemble [path]` | Read the file's recipe, resolve `requires`, sort by `order`, dedup, rewrite the marked region, stamp the hash. Idempotent. |
| `claude-templates check [path]` | Reassemble in memory and compare the hash. Nonzero exit on drift. For pre-commit / CI. |
| `claude-templates list` | List available templates and their `requires`. |
| `claude-templates sync-all` | Reassemble every repo that contains a recipe. |

## Common workflows

### Onboard a repo

1. Add the recipe line above where the block should go:

   ```text
   <!-- templates: core-rules, response-expectations, documentation-style -->
   ```

2. Run `claude-templates assemble`.
3. Move any prose now covered by a template out of your hand-written section.
   Leave only repo-specific identity and deliberate overrides.

### Add a template to a repo

1. Add its `id` to the `<!-- templates: -->` recipe.
2. Run `claude-templates assemble`. Dependencies come in automatically — you do
   not list `requires` yourself.

### Edit shared prose

1. Edit the one template under `.claude/templates/`.
2. Run `claude-templates sync-all` to propagate to every consumer.

### Create a new template

1. Write `.claude/templates/<id>.md` with front-matter (`id`, and `order`;
   add `requires` if it assumes other templates).
2. If it extracts prose that already lives in other templates, delete that
   prose from them and add `requires: [<new-id>]` there instead — never leave
   two copies.
3. `claude-templates list` to confirm it resolves, then add it to any recipe.

### Handle a conflict between a template and a repo

Do not hand-edit inside the markers — the drift check will fail and the next
`assemble` will overwrite you. Instead, add a `## Project overrides` section
below the `END` marker stating the specific point where the template rule is
intentionally not followed. Overrides below win over templates above.

## Drift guard (pre-commit)

`.claude/bin/claude-templates-precommit` blocks a commit when any
`CLAUDE.md` / `AGENTS.md` in the repo has a recipe whose marked region no longer
matches the templates — someone hand-edited inside the markers, or the templates
changed upstream and the file was never re-assembled.

Install it in a consuming repo:

```bash
ln -s ~/Source/dotfiles/.claude/bin/claude-templates-precommit .git/hooks/pre-commit
```

Or in CI, run the scan directly (nonzero exit on drift):

```bash
~/Source/dotfiles/.claude/bin/claude-templates check
```

To run the injector as a bare `claude-templates`, add `~/Source/dotfiles/.claude/bin`
to your `PATH` (or symlink it to `~/.claude/bin` as the `commands` dir already is).

## Guarantees and gotchas

- **Front-matter never reaches the model.** The injector strips it; the emitted
  block is pure prose.
- **Hand-edits inside the markers are lost.** They fail `check` and are
  overwritten by `assemble`. Put durable prose in a template or in an override
  section.
- **The global `~/.claude/CLAUDE.md` is a consumer too** — it has its own recipe
  and marked region, kept lean because it loads every session. Its `global`
  templates are inherited by every repo; never repeat them in a project recipe.
- **`commit-style` is required by `commit-handoff`, not a sibling.** Handoff
  (global) is the personal "I run my own commits" workflow and references the
  Conventional Commits format that `commit-style` defines, so the injector pulls
  `commit-style` in via `requires`. You do not list both.
