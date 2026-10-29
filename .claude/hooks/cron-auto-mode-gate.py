#!/usr/bin/env python3
"""PreToolUse gate: refuse CronCreate unless the session is in auto mode.

Written after the 2026-10-21 overnight todo chain stalled for seven hours. The
job was scheduled from an `acceptEdits` session; at 00:21 it dispatched a
background implementer whose first compound shell command raised a permission
prompt, and nobody was there to answer it until 07:17. A scheduled prompt runs
by definition while the operator is away, so any mode that prompts turns the
first unlisted command into a silent stall. The model that scheduled the job had
every fact needed to see this and did not; a hook does not forget.

Design choices (the failure modes a naive change would reintroduce):
  * Uses `deny`, not `ask`. `ask` resolves silently under permissive modes and
    is a prompt the operator approves on reflex at scheduling time; `deny` hands
    the reason back to the model, which must tell the operator to switch modes.
  * Gates EVERY CronCreate, not only ones whose prompt names a loop. Any
    scheduled prompt may call tools, and guessing which prompts are "safe" from
    their text is the kind of plausible inference that produced the incident.
  * Allows only `auto` and `bypassPermissions`. `default`, `acceptEdits` and
    `plan` all prompt. `dontAsk` does not stall but silently denies, so an
    unattended run fails on its first unlisted command; it is refused too.
  * A MISSING `permission_mode` field DENIES (fail closed), unlike this repo's
    other hooks. The gate exists for the case where the mode cannot be shown to
    be safe, CronCreate is rare, and a loud block costs one mode switch.
    Unparseable stdin still fails open: that is a Claude Code fault, and
    blocking on it would hide the real error behind this one.
  * Checks the mode at SCHEDULING time only. The operator can still switch
    modes before the job fires; `/todo-loop` preflight re-checks at fire time
    with `~/.claude/bin/claude-permission-mode`.
"""
import json
import sys

ALLOWED = {"auto", "bypassPermissions"}

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open on a malformed hook payload; see docstring

if data.get("tool_name") != "CronCreate":
    sys.exit(0)

mode = data.get("permission_mode") or ""
if mode in ALLOWED:
    sys.exit(0)

shown = mode or "unknown (the hook payload carried no permission_mode)"
reason = (
    "Blocked: CronCreate requires auto permission mode; this session is in "
    + shown + ".\n\n"
    "A scheduled prompt runs while the operator is away. In any mode that "
    "prompts, the first command outside the allowlist waits for an answer "
    "nobody gives (2026-10-21: an overnight todo chain stalled seven hours "
    "under acceptEdits).\n\n"
    "Do not schedule the job. Tell the user to switch this session to auto "
    "mode (Shift+Tab until the footer shows it, or restart with "
    "`claude --permission-mode auto`), then ask them to repeat the request. "
    "For /todo-loop, have them run `/todo-loop --check` first."
)

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )
)
sys.exit(0)
