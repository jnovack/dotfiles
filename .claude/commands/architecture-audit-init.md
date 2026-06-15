# /architecture-audit-init

Initialize architecture refactor scaffolding for the current project through a
short guided conversation. The goal is to understand the project well enough to
generate meaningful audit questions — not just a generic template.

---

## Before talking to the user

**Check for a prior discovery file first:**

If `docs/discovery.md` exists, read it. Tell the user: "I found a prior discovery
file. I'll use that as my starting point and skip the discovery conversation — just
confirm anything looks wrong before I generate the scaffolding."

Jump directly to Round 4 (one question about planned additions), then Generation.
Skip Rounds 1–3 entirely.

If `docs/discovery.md` does not exist, suggest running `/discover` first:
"I'd recommend running `/discover` before this — it runs a short conversation to
understand the project and saves a `docs/discovery.md` file I can use here.
Want to do that now, or continue and I'll ask the questions inline?"

If they want to continue inline, proceed with the full Round 1–4 conversation below.
If they want to run `/discover` first, stop here.

---

Run these silently so you already know the shape of the project:

```text
get_architecture_overview()
list_communities()
```

Also collect:
- All entrypoints: `cmd/`, `bin/`, top-level executables, `main.py`, etc.
- All internal packages: `internal/`, `src/`, `lib/`, `pkg/`, etc.
- Primary language and test command.
- Any existing `REFACTOR.md` or `docs/refactor/` — if found, stop and tell the
  user to remove them before re-running.

Hold all of this. Do not mention it yet.

---

## Round 1 — Plain-English Opening

Tell the user: "I found [N] packages and [N] entrypoints. Before I generate
anything, I want to understand the project from your perspective. Three questions:"

Ask these as plain text — not a form, not bullet points, not a checklist.
One at a time if the user seems overwhelmed; all three at once if they seem comfortable:

**Q1 — What it does:**
> "What does this app actually do? Give me the one or two sentence version you'd
> tell a new teammate on their first day."

**Q2 — What's broken:**
> "What part of the codebase makes you wince? Not 'what should be better
> someday' — what actively gets in your way right now when you're trying to
> make a change or debug something?"

**Q3 — What can't break:**
> "What has to keep working no matter what? What would cause an actual problem
> — for you, a user, a downstream system — if you accidentally changed it?"

Wait for answers before proceeding. Do not generate files yet.

---

## Round 2 — Targeted Follow-Ups

Read their answers carefully. Based on what they said, ask 1–3 targeted follow-up
questions from the list below. Only ask what their answers made relevant.
Do not ask all of them. Use judgment.

**If they described a multi-step process or workflow:**
> "You mentioned [the steps]. Does each of those need to run on its own sometimes,
> or do they always run together? And what happens if one fails halfway through —
> does everything stop, or does it limp forward?"

**If they mentioned slowness, long-running tasks, or waiting:**
> "How long does the slow part actually take? And while it's running, can anything
> see what's happening — or does it just go silent until it's done?"

**If they mentioned external services, APIs, or databases:**
> "If that external call fails or is slow, what happens to everything else that
> was in flight? Does it retry, bail out, or just silently produce bad output?"

**If there are multiple entrypoints and the roles aren't obvious:**
> "Looking at your [binary names] — are these meant to be used by the same
> person, or do different types of users run different ones? For example, is
> one for operators and one for end users?"

**If they mentioned data, files, or caching:**
> "When the app fetches data, does it save anything locally so it doesn't have
> to fetch again? Or does it go back to the source every time? And if you
> deleted the database and needed to reload from scratch — would that mean
> re-fetching everything, or is there a local copy somewhere?"

**If they mentioned tests being bad or absent:**
> "What kind of tests exist right now? And is there anything you can run locally
> to verify the whole flow end-to-end without needing a live environment?"

**If they mentioned wanting to add something new:**
> "What's next on your list that the current code isn't ready for? Not a full
> roadmap — just the one thing that's blocked by how it's structured right now."

After their answers, pause and synthesize. Do not jump to generation yet.

---

## Round 3 — Confirm Understanding

Write a short summary (5–8 lines) of what you now understand, in plain English.
Frame it as "here's what I'm going to use to shape the audit" — not architecture
jargon. Something like:

> "OK, so here's what I'm working with: [app] is a [type of thing] that [does X].
> The main pain point is [Y] — [brief reason]. The stuff that can't break is [Z].
> I'm also noting that [any follow-up insight]. Does that sound right, or did I
> miss something?"

Wait for confirmation or correction. If they correct something, update your
understanding and re-confirm. Do not proceed until they say it looks right.

---

## Round 4 — One Final Scoping Check

Ask this one question before generating anything:

> "Last thing: is there anything that's planned but doesn't exist yet — a new
> feature, a new entry point, a different way people will use this — that you'd
> want the new architecture to be ready for? If nothing comes to mind, just say
> none and we'll let the audit surface it."

Then generate immediately after their answer. No more questions.

---

## Generation

Generate all five files using the structural patterns below, informed by
everything learned in the conversation.

---

### REFACTOR.md (project root)

Write sections in this order. Every section is required.

**## Orchestral Operation**

Generic. Verbatim:

> Steps are run one at a time by invoking `/refactor-next`. The orchestrator reads
> this file and the current phase doc, finds the next incomplete step, and spawns
> a subagent at the correct model tier. The subagent writes findings to disk, marks
> the step complete, and returns a synopsis. The orchestrator relays the synopsis
> and waits for the next `/refactor-next` invocation.
>
> **Invoke:** `/refactor-next`
>
> One step per invocation. Codex steps cannot be auto-spawned — the orchestrator
> outputs the prompt as a copyable block for manual Codex execution.

**## Model and Effort Guide**

Generic table with four rows (Haiku / Sonnet / Opus / Codex) and their use cases.
Opus investment table: Synthesis (1.9), Core model design (2.4), Interface contracts
(2.8), Migration sequence (2.9). Codex note about dropping the graph tool line.

**## Intent**

Written from the conversation. Not architectural language — just what the app does,
what the main pain point is, and what this refactor is trying to fix. If the user
said it well in Round 1, quote or paraphrase them directly.

**## Binaries in Scope**

Table: Binary, Status (Existing / Planned), Role.
Populate from discovered entrypoints plus any planned ones from Round 4.
Binary Responsibilities subsection: one plain-English paragraph per binary
describing who runs it and what it does. Use the user's language, not abstractions.
If a frontend/SPA exists: note it's out of scope but must not break.

**## Current Package Inventory**

Table: Package, Current stated purpose (inferred from name + graph communities).

**## Workflow and Domain Notes**

This replaces the abstract "Domain Model" section from the old template.
Write it as: "Here's how the app works based on the conversation."
Use the user's words. Describe the main workflow, the slow parts, the failure modes
they mentioned, and the data/caching behavior if relevant.

If the workflow revealed multi-step execution, document it as a flow:
step names, dependencies between steps, what's optional, what's slow.

If there's a remote/local operator split or any access-level distinction, document it.

If the user said "defer to audit" or couldn't describe it: write a one-paragraph
placeholder and note that Phase 1 should treat this section as a primary deliverable.

**## What Must Not Break**

Populated from Q3 and any follow-up answers. Written as a plain-English list.
Each item: what it is, why it matters (use the user's reason if they gave one).
If "none known yet": write the placeholder and flag it for Phase 1 to identify.

**## Code Standards**

Confirmed: structured logging (library name if detected), context threading on
blocking/cancellable functions. TBD in Phase 1: test framework, linter config.
Test requirement regardless of framework: fast unit tests and full offline end-to-end
tests that don't require a live environment.

**## Session Handoff Protocol**

Generic. Each phase writes its deliverable to `docs/refactor/` before the session
ends. The next agent reads the project conventions doc, REFACTOR.md, and the prior
phase's deliverable. Context does not survive between sessions — the files are the memory.

**## Phase Map**

| Phase | File | Model | Status |
| --- | --- | --- | --- |
| 1 — Architecture audit | docs/refactor/phase1-audit.md | Claude | Not started |
| 2 — Target design | docs/refactor/phase2-design.md | Claude | Not started |
| 3 — Implementation | docs/refactor/phase3-log.md | Codex/Sonnet | Not started |

**## Definition of Done**

Six items: code quality, technical debt cleared, documentation updated, tests added
(unit + offline E2E), coverage ledger updated, ADRs for significant decisions.
Use the project's actual test command and coverage file name.

**## Success Criteria**

Core items plus project-specific ones inferred from the conversation:
- Thin entrypoints
- Single orchestration model
- Independently runnable units (if multi-step workflow was described)
- Explicit lifecycle contracts for long-running operations (if slowness was mentioned)
- Centralized progress visibility (if "goes silent" was mentioned)
- Docs, tests, and contracts synchronized

---

### docs/refactor/phase1-audit.md

**Standard Preamble** — project-specific version. Replace the app name. Always include:
read the project conventions doc first, read REFACTOR.md, use graph tools before file
reads, write findings to disk, mark step complete in both places.

**Step Index table** — five columns: Step, Name, Status, Budget, Model:

| Step | Name | Status | Budget | Model |
| --- | --- | --- | --- | --- |
| 1.1 | Structural overview | Not started | Small | Haiku |
| 1.2 | Package responsibility assessment | Not started | Medium | Sonnet |
| 1.3 | Data persistence and caching audit | Not started | Medium | Sonnet |
| 1.4 | Core workflow audit | Not started | Medium | Sonnet |
| 1.5 | External dependency audit | Not started | Small | Haiku |
| 1.6 | Operator and trigger model audit | Not started | Medium | Sonnet |
| 1.7 | Standards audit | Not started | Small | Haiku |
| 1.8 | Planned additions audit | Not started | Small | Haiku |
| 1.9 | Synthesis | Not started | Medium | **Opus** |

Rename steps 1.3 and 1.4 to match the project's actual concerns.
If there's no caching or persistence concern, rename 1.3 to "Data flow audit."
If there's no multi-step workflow, rename 1.4 to "Business logic audit."

Budget key: Small ≈ graph-only or 1–2 reads. Medium ≈ 3–6 targeted reads.
Model key: Haiku = mechanical. Sonnet = analysis. **Opus** = synthesis, gates Phase 2.

**Step 1.1** — Haiku. Graph-only: `get_architecture_overview()`, `list_communities()`.
Find: community count and meaning, most central packages, isolated packages, gaps
between communities and intended boundaries.

**Step 1.2** — Sonnet. Graph per package: `imports_of`, `callers_of`, `tests_for`.
Read `doc.go` only when graph is ambiguous.
Assess each package: clean single responsibility / reasonable multi-concern / junk drawer.
Populate the assessment table with the packages discovered during init.
Note: "Why Opus" appears on Step 1.9 only.

**Step 1.3** — Sonnet. Adapt to the project's persistence/caching reality.
If caching exists: audit artifact layout, freshness mechanism, extract/load separation,
partial-write detection, per-resource TTL configurability.
If no caching: audit data flow — what is fetched vs. stored, what would happen on
restart or re-run, whether any work is unnecessarily repeated.

**Step 1.4** — Sonnet. Audit the core workflow described in REFACTOR.md §Workflow and
Domain Notes. Verify or contradict the description from the conversation.
Key questions: can individual steps run independently? Where are dependencies hardcoded?
Where does failure policy live? Is progress visible during long-running operations, or
does execution go silent?

**Step 1.5** — Haiku. Find external packages used in long-running operations.
For each: where called, estimated duration, whether a progress hook exists.
Are calls behind an interface or direct? Can a waiting client see progress today?

**Step 1.6** — Sonnet. Audit how work gets triggered.
Is there a shared execution type or does each trigger path (CLI, API, signal, scheduler)
have its own? Which CLI behaviors have no API equivalent? Is the trigger queue shared?
What can a remote or limited operator do that a local operator can't?

**Step 1.7** — Haiku. What test packages and patterns exist? Is there a linter config?
Are there offline end-to-end tests? Recommend a standard for Phase 3.

**Step 1.8** — Haiku. For each planned addition from REFACTOR.md §Binaries in Scope:
what in the current structure would block it? Is there any current code to reuse?

**Step 1.9** — **Opus**. Reads all prior findings, no additional graph queries.
Why Opus: this produces the migration plan Phase 2 and Phase 3 execute against.
Weak synthesis here cascades into every subsequent session.
Produces: architecture diagnosis, structural problems list, proposed target layout,
contract map (public vs. internal), migration plan (checkpointed, ordered).

Each step section has: status/model/budget on one header line, graph queries block,
task as questions, findings subsections that mirror the questions.

---

### docs/refactor/phase2-design.md

Standard preamble: read conventions doc + REFACTOR.md + Phase 1 Step 1.9 synthesis
+ this file. Use graph only to verify Phase 1 findings. Write decisions to disk.

Step Index:

| Step | Name | Status | Budget | Model | Depends on |
| --- | --- | --- | --- | --- | --- |
| 2.1 | Standards decisions | Not started | Small | Sonnet | 1.7 |
| 2.2 | Package ownership map | Not started | Small | Sonnet | 1.2, 1.9 |
| 2.3 | Persistence / data layer design | Not started | Medium | Sonnet | 1.3 |
| 2.4 | Core workflow and lifecycle design | Not started | Medium | **Opus** | 1.4 |
| 2.5 | External dependency adapter design | Not started | Small | Sonnet | 1.5 |
| 2.6 | Execution and trigger model design | Not started | Medium | Sonnet | 1.6, 1.8 |
| 2.7 | Target package layout | Not started | Small | Sonnet | 2.2–2.4 |
| 2.8 | Interface contracts | Not started | Medium | **Opus** | 2.3–2.6 |
| 2.9 | Migration sequence | Not started | Medium | **Opus** | all 2.x |
| 2.10 | ADR list | Not started | Small | Sonnet | 2.9 |

Why Opus on 2.4: core workflow interface and lifecycle vocabulary are the contracts
everything in Phase 3 implements against. Wrong here = rework across every unit and test.
Why Opus on 2.8: Go (or language-equivalent) signatures Codex implements in Phase 3.
Why Opus on 2.9: step ordering determines whether checkpoints leave the build passing.

Each step section: status/model/budget header, Why Opus note where applicable,
task description adapted to the project's concerns, Decisions template with
language-appropriate interface stubs.

---

### docs/refactor/phase3-log.md

Standard preamble: read conventions doc + REFACTOR.md + Phase 2 design docs + this
file. Implement only the assigned step. Run tests after every step. Update coverage
ledger. Create ADRs in `docs/decisions/` when required. Append session log entry.

Model Selection Guide table: Haiku (pre-flight, test runs, file moves), Codex
(boilerplate, implementing a fully specified interface), Sonnet (orchestration,
E2E tests, any step where the design is incomplete), note about Codex not having
graph tool access.

Step Index (starts minimal):

| Step | Description | ADR? | Model | Status |
| --- | --- | --- | --- | --- |
| 3.0 | Pre-flight: confirm tests pass on current code | no | Haiku | Not started |

Note: Steps 3.1+ populated from Phase 2 Step 2.9.

Session Log format (append-only, never edit prior entries):

```text
### YYYY-MM-DD — Step 3.N — [name]
Agent: Claude / Codex / other
Step: complete / partial (stopping point: ...)
Changed: [files or packages]
Tests run: [exact command]
Result: pass / fail / partial
ADR created: [filename or none]
Blockers: [none or description]
Notes: [anything the next agent needs to know]
```

---

### .claude/commands/refactor-next.md

Generate with the project name substituted for "moxfall" in the title and any
project references. Logic is identical:

- Read REFACTOR.md Phase Map → find current phase.
- Read phase doc Step Index → find next Not started step.
- Check prerequisites (1.9 gates on 1.1–1.8; Phase 2 gates on 1.9; Phase 3 gates on 2.9).
- Haiku/Sonnet/Opus: spawn `general-purpose` subagent with correct model and the
  preamble + step section as prompt. Add synopsis instructions at end. Run foreground.
- Codex: output prompt as copyable block, tell user to run manually, wait for confirmation.
- After subagent returns: report step run, model, 3–5 sentence synopsis, blockers,
  next step name. Do not auto-chain.
- Error handling: incomplete findings → leave Not started, report issue. Status/content
  mismatch → flag before proceeding.

---

## After generating

Tell the user:
- The five files that were created.
- Call out anything left as a placeholder that they should review:
  specifically the Workflow and Domain Notes section and the What Must Not Break section.
- If the workflow description is thin because the user said "defer to audit":
  "The audit will discover the structure, but a 10-minute conversation now about
  how the app's main workflow runs would make every audit question sharper. Up to you."
- How to start: "`/refactor-next` — first step is Haiku, graph-only, takes a few minutes."
