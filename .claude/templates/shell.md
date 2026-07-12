---
id: shell
scope: project
order: 56
---

## Shell (POSIX)

- Prefer POSIX `sh`; avoid bashisms unless the file already uses bash.
- Quote all variable expansions.
- Exit early on fatal conditions; print a clear message (e.g. `[FATAL]`) first.
- Do not let optional feature setup crash the process silently — print a
  warning and continue, or exit with a message.
- Do not expand variables inside single quotes in `sed`, `eval`, or `exec`
  contexts without justification.
