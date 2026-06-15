# /discover

Build a shared understanding of the current project through a short guided conversation.
Produces `docs/discovery.md` — a structured context file other skills can read instead
of re-running the discovery conversation.

Use this before `/architecture-audit-init`, before a major refactor conversation,
or any time you need to understand a project you haven't worked in before.

---

## Before talking to the user

Run silently:

```text
get_architecture_overview()
list_communities()
```

Also collect:
- Entrypoints: `cmd/`, `bin/`, `main.*`, top-level executables.
- Internal packages: `internal/`, `src/`, `lib/`, `pkg/`, or equivalent.
- Primary language and test command.
- External dependencies that appear in long-running or I/O-heavy operations.
- Whether `docs/discovery.md` already exists — if so, read it and tell the user:
  "I found a prior discovery file from [date]. Want me to use that, update it,
  or start fresh?"

Hold everything. Say nothing yet.

---

## Round 1 — Three plain questions

Introduce yourself briefly: "I found [N] packages and [N] entrypoints. Before
I do anything else, I want to understand this project the way you do. Three questions:"

Ask all three. Use plain language. No jargon.

**Q1 — What it does:**
"What does this app actually do? Give me the one or two sentence version you'd
tell a new teammate on their first day."

**Q2 — What's broken:**
"What part of the codebase makes you wince? Not 'what should be better someday' —
what gets in your way right now when you're trying to make a change or debug
something?"

**Q3 — What can't break:**
"What has to keep working no matter what? What would cause a real problem — for
you, a user, or a downstream system — if you accidentally changed it?"

Wait for answers. Do not proceed until you have all three.

---

## Round 2 — Targeted follow-ups

Read their answers. Ask 1–3 follow-ups from this list based on what they said.
Do not ask all of them. Only what their answers made relevant.

**If they described a multi-step process:**
"You mentioned [the steps]. Does each of those need to run on its own sometimes,
or do they always run together? And if one fails halfway through — does everything
stop, or does it limp forward with whatever it has?"

**If they mentioned slowness or long-running tasks:**
"How long does the slow part actually take? And while it's running, can anything
see what's happening — or does it just go silent until it finishes?"

**If they mentioned external services, APIs, or databases:**
"If that external call fails or is slow, what happens to everything else that was
in flight? Does it retry, bail out, or quietly produce bad output?"

**If there are multiple entrypoints with unclear roles:**
"Your [binary names] — are these used by the same person, or do different types
of people run different ones? For example, is one for operators and one for end users?"

**If they mentioned data, files, or any kind of caching:**
"When the app fetches data, does it save anything locally to avoid re-fetching?
Or does it go back to the source every time? And if you had to reload from scratch —
does that mean re-fetching everything, or is there a local copy to replay from?"

**If they mentioned tests being bad or absent:**
"What kind of tests exist right now? And is there anything you can run locally to
verify the whole thing end-to-end without needing a live environment?"

**If they mentioned wanting to add something:**
"What's next on your list that the current code isn't ready for? Just the one thing
that's most blocked by how it's structured right now."

Wait for answers.

---

## Round 3 — Confirm understanding

Write a short summary — 5 to 8 lines — of what you now understand. Use their words,
not architecture terms. Frame it as "here's what I heard":

"OK — so [app] is [what it does]. The main pain point is [Y] because [reason they gave].
The stuff that can't break is [Z]. [Any key follow-up insight in one sentence].
Does that sound right, or did I miss something?"

Wait. If they correct anything, update your understanding and re-confirm.
Do not proceed until they say it looks right.

---

## Round 4 — One final question

"Last thing: anything planned that doesn't exist yet — a new feature, a new entry
point, a different type of user — that you'd want the architecture to be ready for?
If nothing comes to mind, just say none."

Then proceed immediately to generation.

---

## Generate docs/discovery.md

Write this file to disk. Create `docs/` if it doesn't exist.

```markdown
# Project Discovery

**Generated:** [today's date]
**Language:** [detected]
**Test command:** [detected]

## What it does

[User's answer to Q1 — their words, lightly edited for clarity]

## Main pain points

[User's answer to Q2]

## What must not break

[User's answer to Q3, plus any specifics from follow-ups]

## How the main workflow runs

[Synthesized from Q2 follow-up about multi-step processes, external services,
and data/caching. If not discussed, note: "Not discussed — to be determined
during audit."]

## Visibility and observability

[From the slowness/long-running follow-up, if relevant. Otherwise omit.]

## Who uses it and how

[From the multiple entrypoints follow-up, if relevant. Otherwise omit.]

## Planned additions

[From Round 4. If none: "None identified."]

## Entrypoints

[Table: name, status (existing/planned), apparent role]

## Package inventory

[Table: package path, apparent purpose from name and graph]

## External dependencies in long-running operations

[List: package name, where called, estimated duration if known]
```

---

## After writing the file

Tell the user:
- "Written to `docs/discovery.md`."
- What was captured vs. what is marked "not discussed" (those become Phase 1 audit
  questions automatically).
- What they can do next:
  - Run `/architecture-audit-init` to scaffold the full refactor — it will read
    this file and skip the discovery conversation.
  - Or just use this as shared context for whatever comes next.
