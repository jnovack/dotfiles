# PLAN: Claude Instruction Templating Machine

A single-source-of-truth system for the prose in `CLAUDE.md` / `AGENTS.md`
across all repos, with a dependency-resolving injector that deduplicates
fragments, and drift detection so files never silently diverge from the
templates.

## Decisions locked

- **`CLAUDE.md` is the canonical per-project file.** `AGENTS.md` references it
  (already corrected). Templates are injected into `CLAUDE.md`.
- **doc.go: two-tier rule wins.** The golang template's "only contract packages
  get a full doc.go" supersedes the old project rule "every package has a
  doc.go". The old line is dropped, not overridden.
- **Plan first, no edits** until this plan is accepted.

## Problem, quantified

- 32 instruction files across 71 repos.
- Generic prose duplicated across repos: `Response expectations` (10 files),
  `smallest correct change` (7), `Mention assumptions` (7), `Read relevant
  files fully` (5), `Preserve existing structure` (3).
- Duplication *inside* the template set:
  - All four `lang-*` templates repeat the same testing philosophy
    (negative cases, smallest test level, regression tests, "don't claim it
    passed unless it ran") and the same `### Validation` skeleton.
  - `ui-defaults.md` and `playwright.md` both own "selectors live in page
    objects".
  - "Read AGENTS.md/CLAUDE.md first" and "don't claim it ran unless it ran"
    appear in `ansible.md`, `lang-golang.md`, and hand-written repo files.
- The global `~/.claude/CLAUDE.md` contains **verbatim copies** of four
  templates (`code-review-graph`, `commit-handoff`, `command-hygiene`,
  `markdown-lint`) — so the global file is itself an un-templated duplicate and
  must become a machine consumer.

## Target architecture

### 1. Template = fragment with front-matter

Every template gains injector-only front-matter (stripped at assembly, never
emitted into the output):

```yaml
---
id: lang-golang
scope: project
requires: [testing-philosophy, command-hygiene]
order: 40
---
```

- `id` — stable name used in manifests and `requires`.
- `scope` — `global` (lives in `~/.claude/CLAUDE.md`, inherited everywhere) or
  `project` (opt-in per repo). See "Scope layering" below.
- `requires` — other templates this one assumes; the injector pulls them in and
  emits each exactly once. This is the deduplication engine.
- `order` — canonical sort key so assembled files look consistent regardless of
  manifest order (core first, language last).

### 2. Manifest lives in the consuming file

Above the injected block, the file declares its own recipe — one source of
truth per repo, no sidecar file:

```text
<!-- templates: core-rules, response-expectations, documentation-style,
     lang-golang, markdown-lint, command-hygiene, commit-handoff -->
<!-- BEGIN TEMPLATES v:1 hash:<sha256> -->
...assembled, deduped, ordered content...
<!-- END TEMPLATES -->
```

- Content **outside** the markers is never touched — that is where
  project-specific prose and deliberate overrides live.
- The `hash` is over the resolved output; `check` recomputes it to detect drift.

### 3. Canonical file layout

```text
# CLAUDE.md

(project identity — Purpose, Loader First, ES Lifecycle, Fixtures, Good
Outcomes: the parts unique to this repo)

<!-- templates: ... -->
<!-- BEGIN TEMPLATES ... -->
(shared prose, assembled)
<!-- END TEMPLATES -->

## Project overrides
(only where a template rule is intentionally not followed — e.g. ES Docker
E2E layout diverging from the golang test-pyramid template. State that it
supersedes the template point above.)
```

### 4. The injector

A script `~/Source/dotfiles/.claude/bin/claude-templates` (mirrored by a make
target), subcommands:

- `assemble [path]` — read the file's `<!-- templates: -->` recipe, resolve
  `requires`, topo-sort by `order`, dedup, concatenate, rewrite the marked
  region, stamp the hash. Idempotent.
- `check [path]` — reassemble in memory, compare hash; nonzero exit on drift.
  For pre-commit / CI.
- `list` — available templates with their `requires`.
- `sync-all` — walk every repo containing a `<!-- templates: -->` recipe and
  reassemble.

Precedent to copy: the beads block in `~/Source/code-review-graph/AGENTS.md`
(`<!-- BEGIN BEADS INTEGRATION v:1 ... hash:... -->`) already proves the
marked, hash-stamped, regenerable-region pattern in this environment.

### 5. Scope layering: global vs project

Claude Code loads **both** `~/.claude/CLAUDE.md` (global) and the repo's
`CLAUDE.md` every session. So a template that lands in both would be present
twice in the loaded context. Deduplication must therefore work *across* the two
files, not only within one.

Each template declares `scope`:

- `scope: global` — belongs in `~/.claude/CLAUDE.md`; inherited by every repo
  automatically. **Project recipes must not list these.**
- `scope: project` — opt-in per repo (language, stack, doc convention).

Injector rules:

- The global file's recipe auto-pulls every `global` template.
- When assembling a **project** file, the injector subtracts the global closure
  from the resolved set: a project template's `requires` on a global-scoped
  template (e.g. `lang-golang` → `testing-philosophy`) is treated as already
  satisfied by the global layer and omitted from the project block.
- `check` warns if a project recipe explicitly names a `global` template.

Scope assignment:

| Global (`~/.claude/CLAUDE.md`) | Project (opt-in per repo) |
| --- | --- |
| `core-rules`, `response-expectations` | `lang-*` (go, dotnet, node, swift) |
| `change-sizing`, `intent-capture` | `ansible`, `playwright`, `ui-defaults` |
| `documentation-style`, `testing-philosophy` | `adr`, `troubleshooting` |
| `markdown-lint`, `command-hygiene` | — |
| `commit-handoff`, `code-review-graph` | — |

Note several behavioral templates (`core-rules`, `change-sizing`,
`intent-capture`, `documentation-style`) are *not* in today's global file but
should be — they govern how work is done everywhere. Phase 3 adds them.

## Template taxonomy after dedup

### Tier 0 — universal core (every repo)

- **`core-rules.md`** *(new)* — smallest correct change, preserve existing
  structure/naming, no unrelated refactors, backward-compatible & default-off,
  read files before editing, **"do not claim tests/commands passed unless
  actually run"** (single home for a rule now scattered across 4+ files). This
  absorbs the project's *Working Style* + *Change Discipline* and the repeated
  "Core rules" preambles in `autossh`/`catchall`.
- **`response-expectations.md`** *(new)* — summarize what changed, note
  assumptions, call out risks. (In 10 files today; not yet a template.)

### Tier 1 — cross-cutting practices (opt-in, language-agnostic)

- `change-sizing.md` *(exists)*
- `intent-capture.md` *(exists)*
- **`documentation-style.md`** *(new)* — why-not-what, relative links, concrete
  runnable examples, document data/JSON shapes. This is the "Documentation
  why-rule" that `intent-capture.md` already references but that has no home,
  and it absorbs the project's *Documentation Style* section.
- `markdown-lint.md` *(exists)*
- **`testing-philosophy.md`** *(new, extracted)* — the language-agnostic testing
  rules currently copy-pasted in all four `lang-*` files. Language templates
  keep only mechanics and `requires: [testing-philosophy]`.
- `commit-handoff.md` *(exists, global)* — your personal "I run my own commits"
  workflow; applies everywhere. `commit-style.md` *(exists)* holds the
  Conventional Commits *format* that handoff already references, so it becomes a
  `requires` of `commit-handoff` rather than a mutually-exclusive sibling.
- `command-hygiene.md` *(exists)*
- `adr.md` / `troubleshooting.md` *(exist)* — document-type templates.

### Tier 2 — language / stack (pick per repo)

- `lang-golang.md`, `lang-dotnet.md`, `lang-nodejs.md`, `lang-swift.md` — slim
  each: pull shared testing philosophy + the `### Validation` skeleton up to
  Tier 1; keep only language-specific mechanics. Add
  `requires: [testing-philosophy]`.
- `ansible.md`, `playwright.md`, `ui-defaults.md` — stack-specific. Fix the
  `ui-defaults` ↔ `playwright` selector-rule duplication (rule lives in
  `playwright`; `ui-defaults` drops it or `requires` it). Move `ansible`'s
  "read AGENTS.md/CLAUDE.md first" into `core-rules`.

## Migration phases

1. **Refactor templates.** Create `core-rules`, `response-expectations`,
   `documentation-style`, `testing-philosophy`; slim the `lang-*` and
   stack templates; fix the selector duplication; add `id`/`requires`/`order`
   front-matter to every template.
2. **Build the injector** (`claude-templates`) with `assemble` / `check` /
   `list` / `sync-all`, dependency resolution, dedup, and hash stamping.
3. **Convert the two canonical files first:** the global `~/.claude/CLAUDE.md`
   and this repo's `CLAUDE.md`. Move ES-specific content above the block; drop
   the "every package doc.go" line (now supplied two-tier by `lang-golang`).
   Verify assembled output reads correctly.
4. **Roll out** to the other ~30 instruction files, one repo at a time, each
   getting a `<!-- templates: -->` recipe; run `sync-all`.
5. **Drift guard:** pre-commit hook and/or CI step running
   `claude-templates check` so a hand-edit inside the markers fails fast and
   points the author back to the template.

## Risks / open questions

- **Front-matter must never reach the model.** The injector strips it; the
  emitted block is pure prose. Confirm in `check` output.
- **Global file bloat.** `~/.claude/CLAUDE.md` loads every session. Its recipe
  should stay lean; it roughly equals today's content, so no net growth.
- **Override precedence.** Convention: project-identity prose above the block
  sets context; a `## Project overrides` region states any point where a
  template rule is deliberately not followed. Document "overrides win" once.
- **code-review-graph scope.** It sits in the global file today, but the graph
  is per-project infrastructure — only repos with the MCP server benefit.
  Decide whether it stays global (harmless where absent) or moves to project
  scope. Leaning global for now to match current state.
- **Ordering guarantees.** If two templates share the same `order`, break ties
  by manifest position, then `id`, for deterministic output.
