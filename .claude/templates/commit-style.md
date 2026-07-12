---
id: commit-style
scope: global
order: 31
---

## Commit Style

All commits must follow Conventional Commits format:

```text
<type>(<scope>): <short summary>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

### Rules

- Scope is optional — `type: subject` is valid; add one only when it clarifies
  the affected area.
- Summary line: imperative mood, no period, ≤72 characters.
- Body (optional): explain the *why*, not the *what*. Wrap at 72 characters.
- Breaking changes: add `!` after type/scope and a `BREAKING CHANGE:` footer.
- Reference issues in the footer: `Closes #123`, `Refs #456`.

### Examples

```text
feat(auth): add OAuth2 PKCE flow

fix(api): handle nil pointer on missing user session

chore(deps): bump golang.org/x/net to v0.38.0
```
