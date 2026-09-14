---
description: Create a Jira ticket written for the assignee — facts, evidence, requirement. No project narration, no cross-referencing unrelated tickets.
---

# jira-ticket.md

Create a Jira issue. The hard part is not the API call, it is writing for the right reader.

## The one rule everything else follows from

**Write for the assignee, not for the person who asked you to file it.**

The reader is a developer who owns that repo, has none of the surrounding context, and wants
to know: what is wrong, how do I see it, what does "done" look like. They did not attend the
conversation that produced the ticket and should not need to.

Everything that does not serve their next action is noise. Noise is not free — it buries the
requirement and makes the ticket feel like someone else's problem.

## Before writing

- **Verify the cause, do not infer it.** Read the actual error, the actual file, the actual
  config. A failing job name is not a diagnosis. If you cannot state the cause in one
  sentence, you have not finished investigating.
- **Confirm the project key and issue type exist** before composing.
- **Issue type:** `Bug` when something is broken now. `Task` when work is needed and nothing is
  broken. Do not use `Bug` for latent risk or scheduled upgrades.
- **Leave it unassigned** unless told otherwise. Do not set priority, labels, components,
  sprint, or epic unless asked.

## Structure

Four sections, in this order. Omit any that has nothing real to say.

1. **What is wrong** — the observable fact, one or two sentences. Lead with it. No preamble.
2. **Evidence** — exactly enough for the reader to confirm it independently: verbatim error
   text, file paths, line numbers, a run or log link. Prefer a fenced block over prose.
3. **Requirement** — what must be true for this to be closed. The acceptance criterion.
   Include a date *only* if the assignee must hit it.
4. **Suggested fix** — optional, and only when you actually have one. Mark it as a suggestion
   and keep it to the change itself.

Title: `<subject>: <what is wrong>`. Specific enough to triage without opening it.

## Do not include

- **Programme or project context the assignee cannot act on.** Migration schedules, cutover
  dates, milestone names, why you happened to be looking. If a date matters, it belongs in
  Requirement as a requirement — not as a reasoning chain about whose deadline it is.
- **Adjacent findings about the same subject.** "While you are in here", "two things to be
  aware of", "worth knowing". If it is a second problem, it is a second ticket. If it is not
  worth a ticket, it is not worth a paragraph.
- **Cross-references to other tickets, unless the reader must act on them.** Link only a
  blocker, a duplicate, a prerequisite, or a parent. **Never link a ticket as a cautionary
  tale, a precedent, or an illustration.** Sending someone to read about a different repo's
  failure wastes their time and makes them doubt their own diagnosis.
- **Reassurance and severity prose.** "Nothing is broken", "not urgent", "low priority".
  Priority is a field. If it is genuinely low, say nothing.
- **How you found it.** Dates, commands run, tools used — unless reproduction requires them.
- **Deference about approach.** "How you sequence it is your call", "the team can decide".
  Filing unassigned already says that. It reads as padding.
- **Meta-commentary about the ticket itself.**

## Length

It should fit on one screen. If it does not, you have written context where requirements
belong. The fix is deleting, not summarising.

## When you have found several problems

File one ticket per problem, each standalone and readable alone. Do not chain them with
"see also" — a reader who needs the other ticket will be told by a real link type (blocks,
duplicates, relates-to set deliberately), not by prose.

Two problems belong in one ticket only when a single change closes both. Say that explicitly
in Requirement.

## Self-check before submitting

- Would a developer who has never heard of this project know what to do?
- Is every sentence about *this* subject and *this* problem?
- Have I linked another ticket? If so, must the reader act on it? If not, cut it.
- Have I explained why I was looking? Cut it.
- Is the cause verified, or inferred from a symptom?

## After creating

Report the issue key, URL, type, and assignee state. Nothing else.
