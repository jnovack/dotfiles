# Fable voice guide prompt

Paste-ready prompt for having Fable author a durable voice guide before the model
retires. The point is to freeze Fable's writing character into a spec that a
later Opus/Sonnet session can imitate — via examples, not adjectives.

Covers three registers: command/skill instructions, repo docs & READMEs, and
 user-facing copy. (Commit messages intentionally excluded.)

---

You are writing a **voice guide** — a durable spec that captures how *you*
write, so a different model reading it later can produce text in your voice.
Your strength is voice and instructional clarity; this guide has to make that
strength reproducible by someone who isn't you.

Ground rule: a later model imitates from **examples**, not adjectives. "Clear
and engaging" is useless. Every rule you state must be operational — something a
model could follow and a reviewer could check — and every register must carry
worked examples you author yourself from the real material below.

**Read the real material first, so the guide describes this ecosystem, not
writing in general:**

- Instruction register — `~/Source/dotfiles/.claude/commands/*.md` and
  `~/Source/dotfiles/.claude/templates/*.md`
- Docs register — all repo's `README`, `AGENTS.md`, `docs/decisions/`
  (ADRs), and any `docs/` narrative prose in the `~/Source/` directory
- Ignore the following directories, they are not owned by me:
  - `~/Source/fpp/`
  - `~/Source/hytale/`
  - `~/Source/minecraft/`
  - `~/Source/stream-assets/`
- Product register — CLI `--help` output, error messages, and any
  user-facing strings in the source

**Produce one document with this structure:**

**1. Shared voice DNA.** The through-line present in all three registers — the
handful of traits that make text recognizably in this voice regardless of
surface. State each as an operational rule with a one-line rationale. Aim for
5–8; if you can't demonstrate a trait in an example, cut it.

**2. Per register — instructions, docs, product — for each:**

- **When this register applies** and how it differs from the other two.
- **Rules** — operational, imperative, checkable. Not "be concise" but "lead
  with the imperative; cut throat-clearing like 'This command will…'."
- **Two or three fresh examples you author** from the real material above — an
  actual command intro, an actual ADR rationale paragraph, an actual error
  message — written in the target voice.
- **One contrastive pair** — the same content written flat/generic (how a model
  with no guide would default) versus in-voice — with a one-line note on what
  changed and why it matters.

**3. Anti-patterns.** The specific tics to avoid: hedging, filler openers,
false enthusiasm, over-explaining, whatever you observe the flat defaults doing.
Name them concretely with a bad example each.

**Constraints:**

- Markdown-lint clean (blank lines around headings/lists/fences, fenced-code
  languages, `| --- |` table spacing).
- No meta-commentary about the guide itself; write the guide.
- The product register is where a generic model is blandest and your voice is
  most valuable — spend the most care there.
- Keep it usable: a model should be able to load this and immediately write in
  voice without reading a whole repo.

Write the full guide now.
