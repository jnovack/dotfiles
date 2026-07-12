# Intent Capture

A rule + a Stop hook that stops intentional decisions from silently reverting across sessions.

## What it is

Claude has no reliable cross-session memory. Code that was written on purpose in one session —
a workaround for a library bug, a deliberately non-obvious ordering, a guard against a race —
looks indistinguishable from an accident to a later session that reads it cold. That later
session "cleans it up," and the fix is gone.

A standing instruction in CLAUDE.md ("always record your intent") doesn't fix this by itself:
honoring it needs the same attention that's failing in the first place. The **Stop hook**
(`hooks/intent-capture-nudge.py`) closes that gap by making the *consideration* unconditional —
it fires at the end of every turn, regardless of what the model remembers to do on its own, and
asks Claude to check its own diff against the rule before the turn is allowed to end.

The **rule** (`templates/intent-capture.md`) is what the hook points Claude back at. It asks for
three things, in order of durability:

1. The *why* inline at the code point, naming the failure mode a naive revert would cause.
2. A named guard test for anything observable at runtime — a red test survives a revert; a
   comment a future session skims past does not.
3. Conversation-level decisions written to persistent memory, so they outlive the session that
   made them. Reserve numbered ADRs for genuine architecture forks with live alternatives.

## How to wire the hook into a project

Add a `Stop` entry to the project's `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/intent-capture-nudge.py\"",
            "timeout": 5,
            "statusMessage": "Checking for uncaptured intent…"
          }
        ]
      }
    ]
  }
}
```

The command above references the script by its path inside *that project's* `.claude/hooks/`
directory. You have two options for where the script itself actually lives:

- **Copy it per-project** (recommended). Copy `hooks/intent-capture-nudge.py` from this dotfiles
  repo into each project's own `.claude/hooks/`. This is the pattern the rest of this repo's
  `.claude/` assets already use (templates get copy-pasted into a project's CLAUDE.md, not
  included by reference), it keeps a project's `.claude/` self-contained and reviewable in that
  project's own git history, and it means a project can diverge (e.g. widen its own source
  pathspec) without touching dotfiles.
- **Reference it by absolute path** into this dotfiles checkout (e.g.
  `"$HOME/Source/dotfiles/.claude/hooks/intent-capture-nudge.py"`). Faster to set up and stays in
  sync automatically, but it breaks for anyone whose dotfiles checkout lives somewhere else, and
  it makes the project's hook behavior depend on a file outside the project's own repo.

Prefer copying unless you are the only person who will ever run this project's hooks.

## Activation caveat

Claude Code's settings watcher only watches directories that already had a `settings.json` at
session start. If you just created a brand-new `.claude/settings.json` (rather than editing an
existing one), the `Stop` hook you just added may not take effect in the current session. Open
the `/hooks` command once, or restart Claude Code, to pick it up.

## Behavior

- Fires **at most once per session** — a `/tmp/claude-intent-nudge-<sha1(session_id)>` sentinel
  file prevents it from nagging on every turn while work stays uncommitted.
- Only fires when the session actually left **uncommitted source changes** behind. It checks
  `git status --porcelain` against a fixed extension list (see the pathspec comment in the
  script) rather than reacting to every change, so doc-only or config-only turns stay silent.
- **Fails open** on every error path — malformed stdin, no git repo, a subprocess timeout, or
  anything else unexpected causes it to exit silently rather than block the turn. A hook that
  blocks spuriously would fight the user on unrelated work; that failure mode is worse than an
  occasional missed nudge.
- Honors `stop_hook_active` (exits immediately if set), so the block it raises resolves in one
  extra turn instead of looping forever.
- It **nudges, it does not verify**. The hook cannot judge whether Claude's response to the nudge
  was actually correct or complete — it only forces the question onto the table. The judgment
  call still belongs to whoever is reading the diff.

## How to disable

Either remove the `Stop` entry pointing at `intent-capture-nudge.py` from the project's
`.claude/settings.json`, or set `"disableAllHooks": true` in that file to turn off every hook in
the project at once.

## How this composes into CLAUDE.md

This repo has no build script or manifest that assembles `templates/*.md` into a project's
CLAUDE.md automatically — composition is manual. To pull the rule into a project, copy the body
of `templates/intent-capture.md` (including its leading `<!-- intent-capture.md -->` marker
comment, which is how the composed file records provenance for each section) into the target
CLAUDE.md alongside whichever other templates that project already uses.
