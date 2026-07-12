---
id: ui-defaults
scope: project
order: 50
---

## UI Defaults

- Default all new or changed UI to be dark-mode-friendly. Respect `prefers-color-scheme`.
- Avoid hardcoded light backgrounds unless explicitly requested.
- Avoid flash-of-light-theme on initial render.
- Use semantic HTML and accessible controls (proper labels, roles, ARIA where needed).
- Prefer responsive layouts. Do not hardcode pixel widths for content areas.
- Keep styling close to the component or page unless the repo already uses shared
  styles.
- Do not assert on pixel positions or computed styles unless visual layout testing
  is an explicit requirement.

Test-selector placement (selectors live in page objects, never inline in
assertions) is covered by the Playwright template — use it for browser tests.
