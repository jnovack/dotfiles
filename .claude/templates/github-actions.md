---
id: github-actions
scope: global
order: 33
---

## GitHub Actions workflows

Never pin an action version from memory. Training data goes stale and
action majors move fast — verify the current release before writing or
editing any `.github/workflows/*.yml`.

- For every `uses: owner/action@vN` in the file, run
  `gh api repos/owner/action/releases/latest --jq '.tag_name'` and use that
  version, not whatever tag comes to mind.
- If `gh api` isn't available or the repo has no releases, check the
  action's `action.yml` for `using: node20`/`node24` to at least confirm
  it isn't pinned to a deprecated runtime (Node 16 actions are EOL).
- Do this for *every* action referenced, not just the first one — a
  workflow with four `uses:` lines needs four checks.
