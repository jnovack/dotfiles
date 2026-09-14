---
description: Merge the current branch's PR, watch the triggered prod deploy workflow, and verify /healthz
argument-hint: "[base-branch]"
---

# /ship-promote

Merge the open PR from the current branch into the base branch, watch the
prod deploy workflow it triggers, then confirm the deployed service is
actually healthy.

Works on any repo using a shared `wf-appdev-azure-container-app`
pipeline, whose retag-and-deploy workflow fires on `pull_request:
closed` (merged) targeting the default branch, and whose deploy jobs echo
`Container App URL: https://...`.

## What to do

### 1 — Guard rails

- Head branch: current branch. Base branch: `$ARGUMENTS` if given, else the
  repo's default branch. If head equals base, stop.
- `gh pr list --head <head> --base <base> --state open --json number,url,mergeable,mergeStateStatus,statusCheckRollup`
- If no open PR: stop, suggest `/ship-pr` first.
- If more than one: stop, ask which number to use.

### 2 — Verify it's actually safe to merge

- `mergeStateStatus` must be `CLEAN` and `mergeable` must be `MERGEABLE`.
- Every entry in `statusCheckRollup` must have succeeded (ignore neutral/
  skipped checks, but any `FAILURE`/`ERROR` blocks).
- If anything is off, report exactly what's blocking and stop — do not merge
  around a red or pending check.

### 3 — Merge

`gh pr merge <number> --merge` — a real merge commit, not squash/rebase, so
the head branch (e.g. `staging`) stays in sync with the base rather than
diverging from it.

Record the merge commit: `gh pr view <number> --json mergeCommit -q .mergeCommit.oid`.

### 4 — Find and watch the triggered deploy workflow

The shared pipeline's retag-and-deploy workflow is attributed to the *head*
branch, not the base, even though it targets the base. Poll (every few
seconds, up to ~30s):

`gh run list --branch <head> --event pull_request --json databaseId,workflowName,status,conclusion,createdAt --limit 10`

Pick the run that started right after the merge (createdAt just after step 3)
whose `workflowName` looks like the retag/deploy pipeline. Watch it:
`gh run watch <id> --exit-status`. If it fails, stop and report the run URL.

### 5 — Discover the deployed Container App URL(s)

Same as `/ship-stage` step 4, against this run's log:

```bash
gh run view <id> --log | grep -oE 'Container App URL: https://[^[:space:]]+' | sed 's/^Container App URL: //' | sort -u
```

### 6 — Verify `/healthz` on every discovered URL

Same criteria as `/ship-stage` step 5: HTTP 200 required, and if the JSON
body has a `status` field it must read `ok` or `healthy` (case-insensitive);
`degraded`/`error`/anything else, a non-200 code, or an unreachable URL all
count as unhealthy. Report exactly which URL failed and why if so.

### 7 — Report

Summarize: PR number/URL merged, merge commit SHA, deploy workflow run +
conclusion, and each Container App URL with its pass/fail verdict.
