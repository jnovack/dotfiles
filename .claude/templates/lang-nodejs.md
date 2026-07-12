---
id: lang-nodejs
scope: project
requires: [testing-philosophy]
order: 62
---

## node.js

### Module system

- Respect the repo's existing choice of ESM (`import`/`export`) or CJS (`require`/`module.exports`). Do not mix them.
- Match the `"type"` field in `package.json` — do not add or remove it.

### Package management

- Use whichever package manager the repo already uses (npm, yarn, pnpm). Do not switch.
- Commit the lockfile. In CI and clean checkouts, install with `npm ci` (or the
  manager's frozen-lockfile equivalent) — never `npm install`, which can silently
  rewrite the lockfile.
- Do not add a dependency without calling it out explicitly. Prefer packages already in `package.json`.
- Audit any new package before adding: `npm view <pkg>` for last publish date and maintenance signals,
  `npm audit` for known CVEs after installing.

### Async and error handling

- Use `async`/`await` throughout. Do not mix with raw `.then()`/`.catch()` chains in the same file.
- Every `async` function that can fail must have error handling at the call site or propagate explicitly.
- Do not swallow errors with empty `catch` blocks. At minimum, log and rethrow.
- Register `process.on('unhandledRejection', ...)` at the application entry point
  to log context before exiting. (Node already crashes on unhandled rejections by
  default — the handler exists for diagnostics, not to keep the process alive.
  Do not use it to suppress the crash.)
- Do not use synchronous `fs` methods (`readFileSync`, `writeFileSync`) in request handlers or hot paths.

### Code style

- `const` by default. `let` only when reassignment is required. Never `var`.
- Import Node builtins with the `node:` prefix (`import fs from 'node:fs'`,
  `require('node:path')`) — unambiguous and immune to registry typosquats.
- Prefer named functions over anonymous arrow functions for non-trivial logic — stack traces are more readable.
- Remove all `console.log` debug statements before committing. Use the repo's structured logger if one exists.
- Do not use `eval`, `new Function()`, or `vm.runInNewContext` with untrusted input.

### Security

- Validate and sanitize all user-supplied input before use in queries, file paths, or shell commands.
- Never pass user input directly to `child_process.exec` — use `execFile` with an argument array instead.
- Do not hardcode secrets, API keys, or credentials. Read from environment variables.
- If the repo is an HTTP server without security headers, flag it and suggest the
  framework-appropriate package (`helmet` for Express, `@fastify/helmet` for
  Fastify) — do not add it silently; dependency additions must be called out.

### Testing

- Match the existing test runner (Jest, Vitest, Mocha, etc.). Do not introduce a second one.
- For a new project with no runner, default to the built-in `node --test` (stable
  since Node 20) — zero dependencies; reach for Vitest/Jest only when the project
  needs their ecosystem (component testing, rich mocking, coverage UI).
- Use fake timers rather than real delays when a test must advance time (the
  no-arbitrary-sleeps rule is in Testing Philosophy).

### Validation

```bash
node --check src/index.js   # syntax check without running
npm test                    # run test suite
npm run lint                # if a lint script exists
```
