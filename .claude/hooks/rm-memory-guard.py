#!/usr/bin/env python3
"""PreToolUse gate: confirm before deleting anything MEMORY.md references.

Written after `.local/PLAN.md` was deleted during a cleanup even though an
auto-memory entry recorded it as "the ONLY copy and it is not recoverable from
git". The warning was in context and went unread. Cross-referencing a delete
against MEMORY.md is one grep; doing it reliably is what this hook is for.

Uses `deny`, not `ask`. `ask` was tried first and is the better fit in principle
— the user is the only one who can weigh a stale memory pointer against a genuine
cleanup — but it resolves silently under permissive permission modes, which is
exactly when an unattended delete is most likely. `deny` blocks unconditionally
and hands the matching memory lines back to the model, which then has to surface
them and get an explicit instruction before retrying. Do not "soften" this back
to `ask` without first confirming the prompt actually appears in the target
session's permission mode.

Design choices (the failure modes a naive change would reintroduce):
  * Fails OPEN on every error path. A guard that blocks all deletes when jq/JSON
    hiccups would be worse than the risk it covers.
  * Matches on BASENAME, not full path. MEMORY.md cites files loosely
    (`.local/CONTEXT.md`, `<repo>/.local/code-review-handoff.md`), so anchoring
    on the exact string the user typed would miss nearly every real hit.
  * Scans every memory FILE, not just MEMORY.md. This is the difference between
    working and not: in the incident above, MEMORY.md's index line pointed at a
    plan in `~/.claude/plans/`, while the "only copy, unrecoverable" sentence
    naming `.local/PLAN.md` was in the memory body. Indexing lines are summaries;
    the warnings live in the bodies.
  * Scans every project's memory dir, not just this repo's. Deletes cross project
    boundaries (dotfiles, shared plans) and the memory that cares may live
    elsewhere.
  * Extracts arguments from the `rm` SEGMENT only, not the whole command line. A
    first version tokenized everything and a compound like
    `rm -f x && echo "=== files added ==="` matched memory prose on the word
    "files". False positives are not a cosmetic problem here: a guard that cries
    wolf on ordinary compound commands is one the reader learns to wave through,
    which is the same outcome as having no guard.
  * Ignores short tokens (< 4 chars) — flags are already dropped, but bare
    fragments would match half of any prose line and train the reader to click
    through.
"""
import glob
import json
import os
import re
import shlex
import sys

MAX_HITS_SHOWN = 6
MIN_TOKEN_LEN = 4

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open

command = str(data.get("tool_input", {}).get("command", ""))
if not command or not re.search(r"(^|[;&|]|\s)rm(\s|$)", command):
    sys.exit(0)

# Split on shell operators FIRST, then tokenize each segment. shlex.split does
# not treat `;` `&&` `|` as operators — it returns "b.py;" as a single token — so
# scanning its output for separator tokens never resets and every word of a
# chained `echo`/`ls`/`jq` is read as an rm argument. That produced a false
# positive on the very command installing this hook.
PREFIXES = {"sudo", "command", "time", "xargs", "env", "nohup"}

candidates = set()
for segment in re.split(r"&&|\|\||[;&|\n]", command):
    try:
        tokens = shlex.split(segment)
    except Exception:
        tokens = segment.split()  # unbalanced quotes from splitting mid-string
    index = 0
    while index < len(tokens) and tokens[index] in PREFIXES:
        index += 1
    if index >= len(tokens) or os.path.basename(tokens[index]) != "rm":
        continue  # this segment does not invoke rm
    for token in tokens[index + 1:]:
        if token.startswith("-"):
            continue
        base = os.path.basename(token.rstrip("/"))
        if len(base) >= MIN_TOKEN_LEN:
            candidates.add(base)

if not candidates:
    sys.exit(0)

hits = []
for memory_file in sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/memory/*.md"))):
    try:
        with open(memory_file, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except Exception:
        continue
    name = os.path.basename(memory_file)
    for line in lines:
        for candidate in candidates:
            if candidate in line:
                hits.append("  [{}] {}".format(name, line.strip()[:160]))
                break
        if len(hits) >= MAX_HITS_SHOWN * 4:
            break  # bounded scan; the reason only shows the first few anyway

if not hits:
    sys.exit(0)

shown = hits[:MAX_HITS_SHOWN]
extra = len(hits) - len(shown)
detail = "\n".join(shown)
if extra > 0:
    detail += "\n  ... and {} more".format(extra)

reason = (
    "Blocked: this delete touches a path referenced in auto-memory. A memory "
    "entry is the usual place a 'this is the only copy' warning lives, and "
    "`.local/` and other gitignored trees cannot be recovered from git.\n\n"
    + detail
    + "\n\nCommand: " + command
    + "\n\nRead the lines above before retrying. If the reference is stale, say so "
    "and update the memory. If it is live, tell the user what the memory claims "
    "and get an explicit instruction — do not delete and report afterwards. To "
    "keep a copy instead, move the file rather than removing it."
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
