---
id: running-codex
scope: global
order: 36
---

## Running Codex

**Run every `codex exec` from inside a spawned subagent**, never as a
backgrounded Bash command in the main session. The agent count in the UI only
counts subagents, so a Codex run started from Bash shows "0 agents" and looks
idle while it works (seen 2026-10-26, a `$todo-design-review` run).

- Spawn one lightweight subagent (`general-purpose`, `model: haiku`). Give it
  the exact `codex exec` command, then have it run Codex in the foreground with
  a long timeout (up to 600000 ms) and wait for it to exit.
- Have the subagent return the exit status, the `-o` last-message file's
  contents, and any `ERROR:` lines from the log. It doesn't interpret or act on
  Codex's findings; I adjudicate them in the main session.
- If a run could take longer than 10 minutes, the subagent backgrounds Codex
  and waits on the process to exit (for example with Monitor), so it stays
  alive and counted until Codex is done.
- Codex's model comes from `~/.codex/config.toml`. Don't pass `-m` unless I
  name a model.
