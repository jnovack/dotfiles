---
id: command-hygiene
scope: global
order: 30
---

## Command hygiene (for a stable permission allowlist)

"Always allow" captures the full command string, so only commands with a
stable, generic prefix become reusable rules. Follow these so approvals stick:

- Run tools from the working directory. Do not pass `-C /abs/path` or absolute
  file paths when a relative path or glob works (`git remote -v`, not
  `git -C /Users/.../repo remote -v`).
- Prefer `tool .`, `tool ./...`, or a glob over enumerating many explicit file
  paths in one invocation (`gofmt -l .`, not `gofmt -l a.go b.go c.go ...`).
- Never inline scripts (`ruby -e`, `bash -c`, `python -c`, `node -e`). They
  can't be safely allowlisted and each string is unique — write a file or use a
  dedicated tool.
- Put the subcommand/verb early and keep flag order conventional so prefix
  rules match (`az ... list`, `az rest --method get ...`).
- Do not append `2>&1` or redirect to a file unless the task needs it. A
  redirect disqualifies the whole command from matching an allow rule; trim
  verbose output at the source instead (`--query`, `-o tsv`, `--top`), which
  stays inside the one command a rule can match.
- Do not join independent commands with `;` or `&&` when each would match an
  allow rule on its own — issue them as separate tool calls in one response.
  They run concurrently, each is matched independently, and no separator
  `echo` is needed. Keep chaining for genuinely dependent commands, and when
  nothing in the chain is pre-approved anyway.
