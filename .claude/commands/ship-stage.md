---
description: Push the current branch, watch its CI deploy workflow, and verify /healthz on the deployed Container App(s)
argument-hint: "[branch]"
---

# /ship-stage

Push the current (or given) branch, watch the build-and-deploy workflow GitHub
Actions triggers for it, then confirm the deployed service is actually
healthy — not just that the workflow went green.

Works on any repo using a shared `wf-appdev-azure-container-app`
pipeline (each deploy job echoes `Container App URL: https://...`).

## What to do

### 1 — Guard rails

- Branch to ship: `$ARGUMENTS` if given, else the current branch
  (`git rev-parse --abbrev-ref HEAD`).
- Determine the repo's default branch:
  `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.
- If the branch to ship equals the default branch, stop — this command is for
  a feature/staging branch, never for pushing straight to the default branch.
- `git status` — if there are uncommitted changes, warn that they will NOT be
  included in this push (only existing commits go out), but proceed.
- `git fetch origin <branch>` then check
  `git log origin/<branch>..<branch> --oneline`. If empty, report "nothing to
  push" and stop.

### 2 — Push

`git push origin <branch>`. Record the pushed commit: `git rev-parse HEAD`.

### 3 — Find and watch the triggered run(s)

- Poll (every few seconds, up to ~30s) until at least one run shows up for
  this exact commit:
  `gh run list --branch <branch> --json databaseId,headSha,workflowName,status,conclusion --limit 20`
- Watch every run whose `headSha` matches the pushed commit AND whose
  `workflowName` looks like a build/deploy pipeline (skip pure lint/format
  workflows): `gh run watch <id> --exit-status`.
- If any of them fails, stop. Report which run failed and its URL
  (`gh run view <id> --json url -q .url`).

### 4 — Discover the deployed Container App URL(s)

For each successful run, pull its log and extract every deployed URL it
printed:

```bash
gh run view <id> --log | grep -oE 'Container App URL: https://[^[:space:]]+' | sed 's/^Container App URL: //' | sort -u
```

Union the URLs across all runs from step 3. If none are found, say so and
stop — there is nothing to health-check.

### 5 — Verify `/healthz` on every discovered URL

For each URL, `curl -s -o <scratch-file> -w '%{http_code}' --max-time 10
"<url>/healthz"` (use the session scratchpad directory for the body file if
one is available, otherwise `mktemp`).

A URL is healthy only if:

- The HTTP status is `200`, AND
- If the response body is JSON and has a top-level `status` field, that
  field's value is `ok` or `healthy` (case-insensitive). No `status` field at
  all is fine. Any other value (`degraded`, `error`, `unhealthy`, etc.) is
  NOT healthy.
- A non-200 code, a connection failure/timeout, or a non-JSON body when a
  `status` field was expected all count as unhealthy.

If any URL is unhealthy, report exactly which one, its HTTP code, and its
body/status value, and stop there.

### 6 — Report

Summarize: branch pushed, workflow run(s) watched (name + conclusion), and
each Container App URL checked with its pass/fail verdict. Suggest `/ship-pr`
next only if everything passed.
