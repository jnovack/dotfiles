---
description: Upgrade all GitHub Actions uses pins to the latest major release; writes .local/REVIEW.ACTIONS.md (modifies workflow files)
---

Update all GitHub Actions workflow files to their latest major release version and produce `.local/REVIEW.ACTIONS.md`.

Scans every file under `.github/workflows/`, upgrades each `uses:` reference to the latest major release, reconciles any interface changes (renamed inputs, dropped outputs, new required fields), and writes a report. This command modifies workflow files — review the diff before committing.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist, create it with:

```text
*
!.gitignore
```

---

## Wontfix pins

Before doing anything else, scan every `uses:` line for a `# wontfix` comment (case-insensitive, with or without a space before the `#`). Examples:

```yaml
uses: actions/checkout@v3  # wontfix: pinned to v3 for Node 16 compat
uses: some/action@abc123   #wontfix compatibility with legacy runner
```

Skip these entirely. Do not look up newer versions. Do not modify the line. Include them in the report table with New Pin = `#wontfix` and the verbatim comment in the Reason column.

---

## Step 1 — Discover

Find every `.github/workflows/*.yml` and `.github/workflows/*.yaml` file. Read all of them. Build a deduplicated list of every `uses:` reference that does NOT have a `# wontfix` comment, noting the current pin for each.

Classify each pin format — this determines the output format when updating:

| Format | Example | Class |
| --- | --- | --- |
| 40-char hex SHA | `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` | `sha` |
| Full semver tag | `actions/checkout@v4.2.2` | `semver` |
| Major-only tag | `actions/checkout@v4` | `major` |
| Branch name | `actions/checkout@main` | `branch` |

---

## Step 2 — Look up latest major releases

For each unique action, use the `gh` CLI — structured output, no HTML scraping, and it handles auth/rate limits. Fall back to WebFetch on the releases page only if `gh` is unavailable or a lookup fails:

```bash
gh api repos/OWNER/REPO/releases/latest --jq '.tag_name'          # latest stable release
gh api repos/OWNER/REPO/tags --jq '.[].name'                      # fallback when the repo doesn't use releases
gh api repos/OWNER/REPO/git/ref/tags/vX.Y.Z --jq '.object | "\(.type) \(.sha)"'  # SHA a tag points to
```

- Identify the highest stable major version and its latest full semver (e.g. major `v4`, latest release `v4.2.2`)
- For `sha`-class pins, resolve the commit SHA the latest release tag points to. If the ref above returns type `tag` (an annotated tag object) rather than `commit`, dereference it: `gh api repos/OWNER/REPO/git/tags/SHA --jq '.object.sha'`

Do not upgrade to pre-release or release-candidate tags unless the action has no stable release at all.

---

## Step 3 — Check interface changes

For each action being upgraded across a major version boundary (e.g. `v3` → `v4`), fetch the action's release notes (`gh api repos/OWNER/REPO/releases --jq '.[] | .tag_name + ": " + .body'`, or WebFetch the release page for long-form notes) or CHANGELOG to identify renamed inputs, removed inputs, new required inputs, changed defaults, and renamed or removed outputs. Cross-reference these against the actual `with:` blocks and downstream `${{ steps.[id].outputs.* }}` expressions in every workflow file that uses the action.

---

## Step 4 — Apply updates

For each action that has a newer major version, update the `uses:` pin using the same format as the current pin (replace like for like):

| Current class | New pin format | Example |
| --- | --- | --- |
| `sha` | SHA of the latest release + version comment | `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2` |
| `semver` | Full semver of the latest release | `actions/checkout@v4.2.2` |
| `major` | Major tag of the latest release | `actions/checkout@v4` |
| `branch` | SHA of the latest release + version comment | `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2` |

Branch pins are unsafe and are always upgraded to SHA format regardless of the repo's prevailing style.

Then apply any interface changes: rename inputs, remove obsolete keys, add new required keys. If a required interface change cannot be resolved automatically, leave a `# TODO:` comment on the affected line and note it in the Reason column of the report.

Do not modify workflow logic, job conditions, secrets references, or anything unrelated to the action pin and directly affected `with:` / `outputs:` fields.

---

## REVIEW.ACTIONS.md Format

```markdown
# Actions Update Report

> Generated: [datetime in localtime — run `date`, do not guess]
> Reviewer: Claude Code
> Scope: .github/workflows/

## Summary

[3–5 sentences: total actions reviewed, how many updated, notable major-version
jumps, interface changes applied, TODOs left for manual resolution]

---

## Changes

One table per workflow file that has any row to report (updated or wontfix).
Omit files and actions where the pin was already at the latest major version.

### .github/workflows/FILE.yml

| Action | Old Pin | New Pin | Reason |
| --- | --- | --- | --- |
| `actions/checkout` | `@v3` | `@v4.2.2` | None |
| `actions/setup-go` | `@v4` | `@v5.3.0` | `go-version-file` default changed to `""` — set explicitly |
| `docker/login-action` | `@v2` | `#wontfix` | pinned to v2 for legacy registry compat |
| `some/action` | `@v1` | `@v2` `# TODO` | required input `token` removed; no clear replacement |

---

Working tree is dirty. Review changes with `git diff .github/workflows/` before committing.
```
