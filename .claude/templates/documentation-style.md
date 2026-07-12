---
id: documentation-style
scope: global
order: 22
---

## Documentation Style

- Comments and docs lead with *why*, not *what*. A reason on the changed lines
  survives refactors; prose that restates the code goes stale the moment the
  code moves.
- Keep examples concrete and runnable.
- When adding a config-driven feature, document the data/JSON shape the code
  expects, not just the flag or option name.
- When behavior is subtle, document the behavior and ordering, not only the
  surface (flags, options, signatures).
- Use relative links in Markdown. Never commit absolute filesystem paths.
- Keep any Markdown you touch lint-clean (see Markdown Lint Rules).
