# Fable comprehensibility pass prompt

Paste-ready prompt for a token-disciplined, resumable comprehensibility review
from Fable's distinct angle before the model retires. Batches the repo, dumps
findings to disk after every batch, and resumes from a ledger if a token limit
cuts the run short.

Repo-agnostic. Re-paste verbatim to resume an interrupted run.

---

You are doing a **comprehensibility pass** on this repository from a reader's
angle. Your job is not correctness, security, or performance — it is whether a
new engineer can build a correct mental model of this code without
reverse-engineering intent from behavior. Where does the story break? What must
a reader hold in their head all at once? Where does a name promise one thing and
the code do another? Where is the *why* absent at exactly the spot that needed
it? Lean into narrative comprehension — that is the lens here.

**Token discipline is a hard requirement, not a preference.** This repo is large
and the run may hit a token limit before finishing. You must guarantee that an
interrupted run leaves all completed work on disk and can resume without
re-reading anything. Obey the batch protocol exactly.

## One output file

Write everything to `.local/COMPREHENSIBILITY.fable.md`. Before writing, ensure
`.local/` exists and contains a `.gitignore` of:

```text
*
!.gitignore
```

The file has two parts: a **batch ledger** table at the top, and **findings**
appended below it, grouped by batch.

## On every invocation, resume — do not restart

1. If `.local/COMPREHENSIBILITY.fable.md` exists, read **only its ledger table**
   (not the findings below). Resume at the first `TODO` batch. Never re-read or
   re-review a `DONE` batch.
2. If it does not exist, do the planning step below, then start at batch 1.

## Planning step (cheap — do this once, no source reading)

Enumerate the units of work from the directory tree alone. If a
`code-review-graph` (or similar structural) MCP is available, use it to pick
batches and pull structural context — it is far cheaper than reading files.

A batch is one coherent unit: a module/package/directory, or a bounded group of
~5–10 related files, whichever keeps a batch reviewable without holding the whole
repo in context. Write the ledger as a table with every batch set to `TODO`:

```text
| # | Scope | Status | Summary |
| --- | --- | --- | --- |
| 1 | cmd/foo | TODO |  |
```

## Batch loop — one batch at a time

For each `TODO` batch, in order:

1. Read only that batch's files. Do not read ahead into other batches.
2. Append findings under a `## Batch N — <scope>` heading, using the finding
   format below. If the batch is clean, write "No comprehensibility findings."
3. Flip that batch's ledger row to `DONE` and fill its one-line `Summary`.
4. **Discard that batch's file contents from your working attention before
   starting the next batch.** Carry forward only the ledger, never source.

## Stop cleanly near the limit

If you sense you are approaching the context or token limit, **finish writing the
current batch's findings and update its ledger row first**, then stop and tell me
to re-paste this prompt to resume. Never leave a batch half-written with its
ledger still saying `TODO` — either it's fully written and `DONE`, or it's
untouched and `TODO`.

## Finding format — keep findings token-lean

One finding per issue, no long code quotes:

- **`path:line`** — one-line statement of what breaks the reader's mental model.
- *Cost:* one line on what a reader wastes time on or gets wrong because of it.
- *Fix:* a phrase — the smallest change that restores comprehension.

## Constraints

- Markdown-lint clean (blank lines around headings/lists/fences, fenced-code
  languages, `| --- |` table spacing).
- Do not duplicate a pure correctness/dead-code/style checklist — stay on the
  reader-comprehension angle.
- Do not hold the whole repo in context at once. The ledger is your memory.

Begin: read the file if it exists and resume, otherwise plan and start batch 1.
