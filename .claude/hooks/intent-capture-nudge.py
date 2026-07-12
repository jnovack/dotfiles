#!/usr/bin/env python3
"""Stop hook: nudge intent capture when a session left source changes.

Enforces AGENTS.md > Change Discipline > Intent Capture. Claude's cross-session
memory is unreliable, and a standing instruction is only honored when Claude
happens to attend to it; this hook makes the *consideration* unconditional by
firing at end-of-turn regardless of what Claude remembers.

Design choices (the failure modes a naive change would reintroduce):
  * Fails OPEN on every error path. A hook that blocks spuriously would fight the
    user on unrelated turns; if anything is off (bad JSON, no git, parse error)
    it exits 0 and stays silent.
  * Nudges at most ONCE per session (a /tmp sentinel keyed by session_id), so it
    reminds rather than nags every turn while work is uncommitted.
  * Honors stop_hook_active so the block it raises resolves in a single extra
    cycle instead of looping.
"""
import sys
import os
import json
import hashlib
import subprocess

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open: never block on malformed input

# Already inside a stop-hook-induced continuation -> let the turn end.
if data.get("stop_hook_active"):
    sys.exit(0)

session = str(data.get("session_id", ""))
project = os.environ.get("CLAUDE_PROJECT_DIR", ".")

# Nudge once per session, not once per turn. Prefix is project-agnostic so the
# same hook file works unmodified across every repo that wires it in.
sentinel = os.path.join(
    "/tmp", "claude-intent-nudge-" + hashlib.sha1(session.encode()).hexdigest()
)
if os.path.exists(sentinel):
    sys.exit(0)

# Only nudge when this session actually touched source. This is a fixed
# extension list, not a "does it look like code" heuristic — it deliberately
# excludes docs/config/data files so the nudge doesn't fire on doc-only turns.
# It covers the languages this dotfiles repo has templates for (see
# templates/lang-*.md): Go, JS/TS, Python, C#, Swift, Ruby, plus Java, Rust,
# and shell as common neighbors. Add an extension here if you add a
# lang-*.md template for a language not yet covered.
SOURCE_PATHSPECS = [
    "*.go",
    "*.js", "*.jsx", "*.ts", "*.tsx",
    "*.py",
    "*.cs",
    "*.swift",
    "*.rb",
    "*.java",
    "*.rs",
    "*.sh",
]
try:
    result = subprocess.run(
        ["git", "-C", project, "status", "--porcelain", "--"] + SOURCE_PATHSPECS,
        capture_output=True,
        text=True,
        timeout=5,
    )
except Exception:
    sys.exit(0)

if result.returncode != 0 or not result.stdout.strip():
    sys.exit(0)

try:
    open(sentinel, "w").close()
except Exception:
    pass  # sentinel is best-effort; worst case is a second nudge

reason = (
    "Intent-capture check (AGENTS.md > Change Discipline > Intent Capture): you "
    "changed source this session. For any intentional or non-obvious behavior you "
    "introduced or changed: (1) put the *why* inline at the code point, naming the "
    "failure mode a naive revert would cause; (2) if it is behavior, add or update a "
    "named guard test that fails on revert; (3) persist any decision reached in "
    "conversation to memory. If nothing you changed qualifies, say so explicitly and stop."
)
print(json.dumps({"decision": "block", "reason": reason}))
sys.exit(0)
