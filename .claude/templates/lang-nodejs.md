<!-- lang-nodejs.md -->
## node.js

### Module system

- Respect the repo's existing choice of ESM (`import`/`export`) or CJS (`require`/`module.exports`). Do not mix them.
- Match the `"type"` field in `package.json` — do not add or remove it.

### Package management

- Use whichever package manager the repo already uses (npm, yarn, pnpm). Do not switch.
- Do not add a dependency without calling it out explicitly. Prefer packages already in `package.json`.
- Audit any new package: check weekly downloads, last publish date, and known CVEs before adding.

### Async and error handling

- Use `async`/`await` throughout. Do not mix with raw `.then()`/`.catch()` chains in the same file.
- Every `async` function that can fail must have error handling at the call site or propagate explicitly.
- Do not swallow errors with empty `catch` blocks. At minimum, log and rethrow.
- Register `process.on('unhandledRejection', ...)` at the application entry point — never leave it absent.
- Do not use synchronous `fs` methods (`readFileSync`, `writeFileSync`) in request handlers or hot paths.

### Code style

- `const` by default. `let` only when reassignment is required. Never `var`.
- Prefer named functions over anonymous arrow functions for non-trivial logic — stack traces are more readable.
- Remove all `console.log` debug statements before committing. Use the repo's structured logger if one exists.
- Do not use `eval`, `new Function()`, or `vm.runInNewContext` with untrusted input.

### Security

- Validate and sanitize all user-supplied input before use in queries, file paths, or shell commands.
- Never pass user input directly to `child_process.exec` — use `execFile` with an argument array instead.
- Do not hardcode secrets, API keys, or credentials. Read from environment variables.
- Set `helmet` (or equivalent security headers) if the repo is an HTTP server and does not already have it.

### Testing

- Match the existing test runner (Jest, Vitest, Mocha, etc.). Do not introduce a second one.
- Each test must be independent — no shared mutable state between tests.
- Mock external I/O (HTTP, database, filesystem) at the boundary, not deep inside implementation code.
- Do not use `setTimeout` or arbitrary delays in tests. Use fake timers or proper async patterns.

### Validation

```bash
node --check src/index.js   # syntax check without running
npm test                    # run test suite
npm run lint                # if a lint script exists
```

Do not claim tests pass unless `npm test` was actually run and exited 0.
