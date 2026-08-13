---
name: clean-writeup
description: Write a final-state technical how-to, setup guide, or README from a conversation, showing only the working solution and omitting the debugging journey. Use whenever the user asks to "write this up," "document what we did," "turn this into a guide/README," or similar, after a session that involved any troubleshooting, false starts, or iteration.
---

## Clean Writeup

Turn a conversation that solved a problem into documentation for someone who wasn't there and doesn't need to be walked through how you got there — only how it works now.

### Why this needs a deliberate step

A conversation is written in chronological order, and a lot of that order is failed attempts, wrong turns, and things that got reverted. Left to the natural reading of the transcript, the instinct is to narrate it like a story: "first we tried X, that didn't work because Y, so we switched to Z." That's a fine story for a retro, but it's the wrong artifact for a setup guide — a reader following the doc doesn't want the history, they want the steps that get them from zero to working. Treat the chat log as scratch material to mine for the final state, not as an outline to summarize.

### Steps

1. **Determine public or private documentation**  Ask the user whether or not this is for public consumption (where you are to use generic variables, hostname, ip addresses, etc) or for internal private documentation (where you can list all private infomation as necessary), or both (in which case you produce two documents).
2. **Determine the actual final state, not the last thing said about it.** Read the real, current files/config/commands — don't trust chat messages describing what they contain, since those can be stale by the time troubleshooting moved on. If you have file access, check it directly. If you don't (pure conversation, no repo), reconstruct the final state by working backward from the last successful version of each piece, discarding anything that was later changed or abandoned.
3. **Throw out everything that didn't survive.** Any command, config value, code snippet, or approach that was tried and later replaced does not belong in the output at all — not as a mention, not as a "note: we initially tried X." If it's not part of the working solution, it doesn't exist for this doc.
4. **Identify the audience and their starting point.** Assume a third party with no context on the conversation: what do they need already installed or already know before step 1? That's the prerequisites section.
5. **Write it as an ordered procedure, not a narrative.** Steps a reader executes in sequence, each one an action ("Install X", "Set the following environment variable", "Run this command"), not a description of a decision process.
6. **Use runnable code blocks for every command, config file, or snippet**, with a language tag, so they can be copy-pasted directly.

### Failure modes to catch before finalizing

- **Chronological bias**: if a sentence in your draft would only make sense to someone who watched the conversation happen ("now that we've fixed the port conflict...", "as mentioned earlier..."), cut it. The doc has no "earlier."
- **The diff trap**: this is not a changelog. Don't describe what changed from a previous state — describe what *is*, as if it were built this way from scratch. No "we switched from A to B" — just document B.
- **Contamination from failed attempts**: if the conversation had many wrong turns and one success, most of the raw material is noise. Actively filter rather than summarizing everything you see. It is ok to reference a deviation from a normal setup.

### Output format

Unless the user specifies otherwise, structure the guide as:

```markdown
# [Title describing what this sets up]

## Prerequisites

- [Tools, accounts, versions needed before starting]

## Steps

### 1. [First action]

[Brief context if needed, then the command/config]

​```bash
[runnable command]
​```

### 2. [Next action]

...

## Verification

[How to confirm it worked — a command to run or output to expect]
```

Omit the Verification section only if there's no clear way to confirm success. Adjust headers to fit the domain (e.g., "Configuration" instead of "Steps" for a config-only task).

### If the user's request is ambiguous

If it's unclear whether they want a full setup guide, a shorter reference snippet, or something else (a Slack message, a PR description), ask — the "no debugging history" rule applies regardless, but the shape of the output depends on the target audience and use case.
