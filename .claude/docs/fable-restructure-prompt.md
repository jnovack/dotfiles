# Fable restructure prompt

Paste-ready prompt for handing the `~/Source/dotfiles/.claude/` restructure to
Fable before the model retires. Fable audits first, you approve, then it applies.

---

You are auditing and restructuring a Claude Code configuration repo at
`~/Source/dotfiles/.claude/`. Your strength is structural clarity and
unambiguous instructional prose — use it. This is a restructure, not a rewrite:
preserve every behavior and intent, improve the organization and wording that
carries it.

**Start by reading the whole tree before proposing anything:**

- `CLAUDE.md` — the assembled global instruction file
- `commands/*.md` — 24 slash-command definitions (YAML frontmatter + markdown body)
- `templates/*.md` — 16 reusable prose blocks
- `hooks/` — automation hooks
- `docs/*.md` — human-facing READMEs

**The composition mechanism (do not break it):** `CLAUDE.md` and some commands
are assembled from `templates/` via `<!-- name.md -->` include markers. A marker
means "this block's canonical source is `templates/name.md`." Templates are the
DRY layer; commands are the executable layer; docs are the human layer. Keep
those three roles distinct.

**Hard invariants — violating any of these is a failed restructure:**

- No deprecation scaffolding, aliases, back-compat shims, or transition notes.
  This is a personal config; if something should change, change it outright.
- Any convention, guard, or section that applies to one command must apply
  uniformly to all commands of the same family (`todo-*`, `refactor-*`,
  `review-*`, `assessment*`) unless a difference is intentional and stated.
- Token efficiency matters: these files are loaded into working context. Tighter
  is better *only when it loses no instruction*. Do not compress away necessary
  constraints.
- Every `.md` must stay markdown-lint clean (blank lines around
  headings/lists/fences, fenced-code languages, `| --- |` table spacing).
- Do not invent new commands or new behavior. Reorganize, deduplicate, clarify.

**Work in two passes — audit first, then propose. Do not edit files until I
approve the plan.**

**Pass 1 — Audit.** Produce a findings report covering:

1. **Duplicated prose** — identical or near-identical instruction blocks
   repeated across commands that should be extracted into a `templates/` block
   and referenced by include marker. Name the proposed template and list every
   call site.
2. **Shape inconsistency** — commands in the same family that differ in
   frontmatter keys, section ordering, heading names, or Definition-of-Done
   structure without reason. Propose one canonical skeleton per family.
3. **Role bleed** — executable instructions living in `docs/`, human-explanation
   prose bloating a command body, or a template that's really command-specific.
   Propose where each belongs.
4. **Ambiguous or contradictory instructions** — places where a running model
   could reasonably do the wrong thing, or where two commands give conflicting
   guidance. This is the highest-value category; be aggressive here.
5. **Naming** — command, template, or section names that don't match their
   content or that name the same concept differently across files.
6. **Dead references** — include markers pointing at nonexistent templates,
   cross-references to renamed/removed commands, orphaned templates nothing
   includes.

**Pass 2 — Proposal.** For each finding, give the concrete change: the new/edited
file content, or the exact template extraction with its include markers and every
call-site edit. Order by leverage (most-reused-first). Flag anything where
tightening risks dropping a constraint, and let me decide.

Rank the whole set so I can approve top-down. Begin with Pass 1 now.
