---
id: troubleshooting
scope: project
order: 42
---

## Troubleshooting Documentation

Troubleshooting docs live at two levels:

- `TROUBLESHOOTING.md` — the main page: an index and a short entry per known issue.
- `docs/troubleshooting/<SLUG>.md` — a deep-dive page for issues complex enough to warrant
  step-by-step diagnostic commands.

### When to add an entry to TROUBLESHOOTING.md

Add one when:

- You are explicitly asked to create a troubleshooting document.
- A real failure occurred in this repo and a fix was found.
- The error message alone would not tell an operator what to do.
- The fix is non-obvious, multi-step, or would be forgotten without documentation.

Do NOT add entries for: errors with self-explanatory messages, issues covered in upstream
documentation, or hypothetical failures that have never occurred.

### When to create a docs/troubleshooting/ deep-dive

Create one when the issue requires human diagnosis before the fix can be applied — i.e. the
operator must run commands to gather information, interpret the output, and make a judgment call
before acting. Simple two-command fixes belong only in TROUBLESHOOTING.md.

### TROUBLESHOOTING.md format

```markdown
# Troubleshooting

## Index

- [Short title](#anchor) — One-sentence description of the symptom.
- [Short title](#anchor) — One-sentence description of the symptom.

---

## Short title

**How it presents.** One or two sentences describing the specific observable signal — the exact
CLI output, error string, metric, or log line that makes this issue identifiable. Be precise
enough that an operator can grep for it or match it by eye without ambiguity. "Service is down"
or "cluster is red" is not sufficient; name the field, flag, or message that distinguishes this
failure from others that look similar.

**Fix.** What to run, in order. Use fenced bash blocks. If the fix requires diagnosis first or
has branching paths, end with a link to the deep-dive doc.

See [docs/troubleshooting/SLUG.md](docs/troubleshooting/SLUG.md) for a full walkthrough.
```

Rules:

- Index entries come first, before any H2 sections, and link to anchors within the same file.
- Each section has exactly two bold lead-in paragraphs: **How it presents.** and **Fix.**
- Keep each section short enough to read in under 30 seconds. All depth belongs in the deep-dive.
- HR (`---`) between every section.

### `docs/troubleshooting/<SLUG>.md` format

```markdown
# Title (noun phrase describing the problem, not the fix)

## Background

Why this can happen — the underlying mechanism, not just the symptom. Explain what Docker/the
framework/the system was doing that led to this state, so the operator understands whether the
fix applies to their situation.

## Symptoms

What the operator sees. Include:

- Literal CLI output with fenced code blocks.
- Which field or value is the key indicator.
- How to distinguish this issue from similar-looking ones.

## Diagnosis

Step-by-step commands an operator can run to confirm the root cause before applying the fix.
Each step should explain what to look for in the output and what it means.
Number the steps. Do not skip steps that seem obvious — an operator without context will need them.

## Fix

Numbered steps. Every command in a fenced bash block. Include verification commands after
destructive or state-changing steps so the operator can confirm the step worked before continuing.
If the fix must be repeated per-node or per-instance, say so explicitly.

## Prevention

What change (config, process, tooling) would have prevented this issue. Link to the relevant
config file or Makefile target if applicable.
```

Rules:

- Written for a human operator working without AI assistance. Do not assume they have context
  from the incident that produced this document.
- Every command must be runnable verbatim. No placeholders like `<your-value>` unless the
  value is genuinely site-specific and cannot be derived from the repo.
- Diagnosis and Fix are separate sections. Operators need to confirm root cause before acting.
- Do not editorialize. Record what happened and what worked.
