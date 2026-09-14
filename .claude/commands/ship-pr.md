---
description: Open a PR from the current branch to the repo's default branch, summarizing the commits it adds
argument-hint: "[base-branch]"
---

# /ship-pr

Open the promotion PR for the current branch — e.g. `staging` → `main` — so
it's ready to merge with `/ship-promote`.

## What to do

### 1 — Guard rails

- Head branch: current branch (`git rev-parse --abbrev-ref HEAD`).
- Base branch: `$ARGUMENTS` if given, else the repo's default branch
  (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`).
- If head equals base, stop.
- `git fetch origin <base> <head>`, then compare `origin/<head>` to local
  `<head>`. If local is ahead of `origin/<head>`, warn that the branch hasn't
  been pushed yet and suggest `/ship-stage` first — proceed only once they
  match (a PR is built from what's on the remote, not local commits).

### 2 — Check for an existing PR first

`gh pr list --head <head> --base <base> --state open --json number,url`

If one is already open, report its URL and stop — never open a duplicate.

### 3 — Draft the PR

`git log origin/<base>..origin/<head> --oneline` to see every commit this PR
would add (not just the latest one — summarize the whole set).

- Title: under 70 characters, describing the overall change.
- Body: a short "Summary" section (why, not just what — pull the reasoning
  from the commit bodies where they have it) and, only if this conversation
  actually ran them, a "Test plan" checklist of what was verified (build,
  tests, staging health, etc.). Do not claim verification that didn't happen.

### 4 — Create it

`gh pr create --base <base> --head <head> --title "..." --body "..."`

Print the resulting PR URL and mention `/ship-promote` as the next step.
