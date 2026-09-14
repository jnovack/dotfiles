---
description: Print the reference guide for the ship command set
model: haiku
---

# /ship-help

Display the reference guide for the ship command set.

## What to do

Print the following verbatim:

---

```text
════════════════════════════════════════════════════
 Ship Commands — Reference Guide
════════════════════════════════════════════════════

PIPELINE
────────
Three stages, each its own command, meant to be run in order:

  /ship-stage → /ship-pr → /ship-promote

  ship-stage    Push the branch, watch its deploy workflow,
                verify /healthz on what it deployed.
  ship-pr       Open the promotion PR (e.g. staging → main).
  ship-promote  Merge the PR, watch the prod deploy workflow,
                verify /healthz on prod.

SCOPE
─────
Generic — not tied to one repo. Works on any repo using a shared
`wf-appdev-azure-container-app` pipeline: branches, the PR, and
Container App URLs are all discovered at run time via `git`/`gh`,
nothing is hardcoded.

COMMANDS
────────
  /ship-stage [branch]
    Push <branch> (current branch if omitted). Refuses to run on
    the repo's default branch. Watches every CI run matching the
    pushed commit, greps its log for "Container App URL: https://",
    and health-checks each one found.
    Next: /ship-pr

  /ship-pr [base-branch]
    Open a PR from the current branch to <base-branch> (the
    repo's default branch if omitted). Refuses to duplicate an
    already-open PR. Title/body are drafted from the actual commit
    range, not just the latest commit.
    Next: /ship-promote

  /ship-promote [base-branch]
    Find the open PR for the current branch, refuse to merge
    unless mergeStateStatus is CLEAN and every check succeeded,
    merge it with a real merge commit (never squash/rebase — keeps
    the head branch in sync with base), watch the deploy workflow
    the merge triggers, and health-check every Container App URL
    it deployed.
    Next: nothing — this is the last stage.

  /ship-help
    Print this guide.

GUARD RAILS
───────────
  • Every command refuses to run with head == base branch.
  • ship-stage warns (but proceeds) if the working tree is dirty —
    only committed work goes out.
  • ship-pr checks origin/<head> matches local <head> before
    opening a PR; a local-only commit means push first.
  • ship-promote checks mergeable + mergeStateStatus + every
    statusCheckRollup entry before merging — never merges around a
    red or pending check.

/healthz CONTRACT
─────────────────
A discovered URL is healthy only if:
  • HTTP status is 200, AND
  • if the body is JSON with a top-level "status" field, its value
    is "ok" or "healthy" (case-insensitive) — anything else
    (degraded, error, unhealthy, ...) fails it.
  • No "status" field at all is fine as long as HTTP is 200.
  • A non-200 code, timeout, or connection failure is unhealthy.

Note: this is stricter than some services' own health contract —
e.g. canary's /healthz can legitimately return 200 with
"status":"degraded" for a non-critical dependency failure. These
commands treat that as a failure and stop the pipeline rather than
pass it through.

════════════════════════════════════════════════════
```
