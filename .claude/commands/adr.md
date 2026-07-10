---
description: Create a new Architecture Decision Record in docs/decisions/ and update the index
---

# ADR.md

Create a new Architecture Decision Record in `docs/decisions/`.

Perform the following tasks:

- inspect `docs/decisions/`
- pick the next sequential ADR number using four digits (`0001`, `0002`, etc.)
- create a kebab-case filename from a short summary of the last executed adr or plan and any follow-up.
- if more than one major topic was discussed or fixed, please create individual files or major topics
- Write the ADR file directly in `docs/decisions/`.
- After creating or updating an ADR, update `docs/decisions/README.md`.
- Add a new row to the summary table with the format: `| <adr filename> | Title | Status | Date |`.
- Add an "ADR" tag in the comments near all relevant functions or decision points within the code
  with `adr/NNNN-<kebab-title>.md`.

Rules:

- Prefer repo-specific reasoning over generic architecture language.
- If rejecting an option, explain why it is wrong for this repo, not just why it is imperfect.
- If facts depend on investigation, include exact dates.
- Keep sections short and concrete, provide only as much context as necessary to understand the decision.

The ADR must follow this format exactly:

```md
# ADR {{number}}: {{title}}

- Status: {{Accepted|Rejected|Superseded|Draft}}
- Date: {{YYYY-MM-DD}}

## Context

{{Summarize the problem that necessitated this decision and the final
state reached. Do NOT narrate the debugging journey, intermediate
fixes, or superseded approaches. Write as if the reader only needs
to understand why the decision exists, not how you got there.}}

## Findings

{{State only facts that directly support the final decision.
Omit dead ends, failed attempts, and anything that was later reversed.}}

## Alternatives Considered

{{List as many alternatives discussed.}}

### Option 1: {{name}}

{{Accepted or rejected? Why?}}

### Option 2: {{name}}

{{Accepted or rejected? Why?}}

## Decision

{{State the final decision directly.}}

## Consequences

### Positive

- {{Benefit}}
- {{Benefit}}
- {{Benefit}}

### Tradeoffs

- {{Cost or limitation}}
- {{Cost or limitation}}
- {{Cost or limitation}}

## What Replaces It

{{If this ADR rejects or removes an approach, state what the repo will do instead.}}

## Revisit Criteria

{{State when this ADR should be reconsidered, if ever.}}

## References

- [{{relevant file or doc}}]({{relative-link}})
- [{{relevant file or doc}}]({{relative-link}})
- [{{relevant file or doc}}]({{relative-link}})
```
