---
description: Audit dependency hygiene (floating pins, stale versions, Dependabot/Renovate coverage); writes .local/REVIEW.DEPS.md
argument-hint: [path]
---

Review all package dependency declarations and produce `.local/REVIEW.DEPS.md`.

If a path argument is provided, scope discovery to that path. Otherwise scan the full repository.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist, create it with:

```text
*
!.gitignore
```

---

## Files to Scan

Read all of the following that exist in scope:

**Package manager manifests and lockfiles:**
`go.mod`, `go.sum`, `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `requirements.txt`, `pyproject.toml`, `Pipfile`, `Pipfile.lock`, `Cargo.toml`, `Cargo.lock`, `Gemfile`, `Gemfile.lock`, `composer.json`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `*.csproj`, `*.nuspec`

**Automated update configuration:**
`.github/dependabot.yml`, `.github/dependabot.yaml`, `renovate.json`, `.renovaterc`, `.renovaterc.json`

---

## Scope

For every dependency found, check:

1. **Version pinning** — is the dependency pinned to a specific version, a range, or floating (`latest`, `*`, `^`, `~`, `>=`)? Floating pins allow silent breaking updates without any code change.

2. **Dependabot / Renovate coverage** — is automated dependency update tooling configured? If neither Dependabot nor Renovate is configured, flag it. If configured, verify it covers all ecosystems present in the repo — a config that handles npm but ignores Go modules is partial coverage.

3. **Stale major versions** — a dependency pinned at major version N where the manifest or lockfile provides evidence that N+1 or higher exists (e.g. a different package in the same ecosystem references a newer release). Do not fabricate version information; note that `npm audit`, `go list -m -u all`, `pip-audit`, `cargo audit`, or equivalent must be run for authoritative latest-version and CVE data.

4. **Known-vulnerable version patterns** — flag version ranges known to contain high-profile CVEs if you can identify them with confidence from the version string alone. Do not invent CVE IDs; say "run [audit tool] to check for known CVEs in this range" when uncertain.

---

## Breaking-Change Assessment

For each finding, assess upgrade risk:

| Version change | Default risk | Notes |
| --- | --- | --- |
| Patch bump (x.y.Z) | None | Bug fixes only; safe to update |
| Minor bump (x.Y.z) | Low | Additive for semver-compliant packages |
| Major bump (X.y.z) | High | Assume breaking; check CHANGELOG or migration guide |

For each High finding, grep the codebase for direct usages of the affected package and list what would need to be reviewed after an upgrade.

---

## Ground Rules

- Do not fabricate CVE numbers or security vulnerability claims. If a version looks old, say "run `[audit tool]` to check for known CVEs."
- Do not flag a dependency as outdated unless there is concrete evidence in the manifest or lockfile — do not guess at latest versions.
- If Dependabot or Renovate is fully configured for an ecosystem, lower the severity of stale-version findings in that ecosystem by one level.
- If a file has no dependency issues, omit it from the report.

---

## Output Instructions

- Finding ID format: `#ECOSYSTEM-TYPE-NN`
  - ECOSYSTEM: 2–5 char uppercase abbreviation of the package ecosystem (e.g. `GOMOD`, `NPM`, `PY`, `CARGO`, `GEM`, `NUGET`)
  - TYPE: 2–5 char uppercase abbreviation of the issue class: `UNPIN` (floating version), `STALE` (behind current), `BREAK` (major version gap), `AUTO` (missing automation coverage)
  - NN: 2-digit 1-based integer, incrementing globally across the entire report
    (never resets per ecosystem-type pair)
  - Example IDs: `#GOMOD-STALE-01`, `#NPM-UNPIN-02`, `#PY-AUTO-01`
- For the `Generated:` timestamp, run `date` — do not guess the datetime.
- No encouraging commentary or meta-notes. Keep findings dense and actionable.

---

## REVIEW.DEPS.md Format

Produce REVIEW.DEPS.md with the following structure:

### Header

```markdown
# Dependency Review

> Generated: [datetime in localtime]
> Reviewer: Claude Code
> Scope: [manifests reviewed]
```

### Summary

3–5 sentence summary of dependency hygiene, highest-risk items, and automation coverage.

### Finding Index

| ID | Severity | File | Dependency | Title |
| --- | --- | --- | --- | --- |
| #GOMOD-STALE-01 | 🟡 Medium | `go.mod` | `golang.org/x/net` | Three minor versions behind |
| #NPM-AUTO-01 | 🟡 Medium | `package.json` | (all) | No Dependabot or Renovate configured |

### Findings by File

One block per file that has findings, ordered by highest severity in that file.

#### 🟡 Medium — #GOMOD-STALE-01 — [short title]

**Line(s):** 14

**Dependency:** `golang.org/x/net`

**Current:** `v0.52.0`

**Issue:** Description of the concern.

**Breaking risk:** Low — minor version bump; additive changes expected.

**Local impact:** [which packages or files import this directly]

**Fix:**

```bash
# exact command or replacement
```

**Automation:** [is Dependabot/Renovate configured for this ecosystem? would it have caught this?]

---

### Severity Reference

| Level | Meaning |
| --- | --- |
| 🔴 Critical | Known CVE in a dependency used in a security-sensitive path |
| 🟠 High | Major version gap with likely breaking changes |
| 🟡 Medium | Moderately stale minor version, missing automation coverage, or floating pin |
| 🔵 Low | Minor version drift on a non-security-sensitive dev dependency |

### Quick Wins

A bulleted list of the 3–5 highest-leverage changes — things that eliminate the most risk or close the most automation gaps for the least effort.
