#!/usr/bin/env python3
"""PreToolUse/PostToolUse gate: query the knowledge graph before text search.

Enforces CLAUDE.md > MCP Tools: code-review-graph ("ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read"). That rule was ignored
for an entire session despite being in context the whole time — ~289k tokens went
to subagent exploration and shell greps that two `file_summary` calls later
replaced. A standing instruction is only honored when the model attends to it;
this hook makes the first graph call unconditional.

Two modes, one script so both share the sentinel path formula:

  mark   PostToolUse on mcp__code-review-graph__* — records that the graph was
         consulted in this session.
  check  PreToolUse on Grep/Glob (and `grep` via Bash) — denies until `mark` has
         fired at least once.

SELF-ARMING, so it is safe to install globally: the gate only engages in a repo
that actually HAS a graph. `code-review-graph status` reports `Nodes: 0` where
none has been built, and the answer is cached per session (one ~0.15s subprocess,
then a stat). Without this, installing globally would block Grep/Glob forever in
every repo with no graph — there would be no way to set the unlock sentinel.

Design choices (the failure modes a naive change would reintroduce):
  * ONE graph call unlocks the whole session. The rule permits falling back to
    text search when the graph does not cover something; the point is to make
    checking the graph the first move, not to ban grep. A per-call gate would
    fight legitimate work on markdown, logs and fixtures.
  * Fails OPEN on every error path (bad JSON, unwritable /tmp, missing or broken
    `code-review-graph` binary, MCP server down). A search tool that breaks
    because an unrelated dependency is unhealthy is worse than the problem being
    solved — and the MCP server does go down. Anything unclear means allow.
  * CLAUDE_SKIP_GRAPH_GATE=1 disables it outright. A guard with no escape hatch
    gets removed wholesale the first time it misfires.
  * For Bash it re-checks that the command really is a text search, rather than
    trusting the settings.json `if` filter to have selected one. Correctness must
    not depend on an unverified harness feature: if `if` were ignored, this hook
    would otherwise block EVERY shell command until a graph call happened —
    `git status`, `go test`, everything.
  * The sentinel is keyed by session_id, so a new session re-arms the gate. The
    failure being prevented is per-session inattention, not a one-time mistake.
  * `mark` never inspects tool_name: it is registered behind a matcher that
    already selects graph tools, and re-deriving that here would let the two
    drift apart silently.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open: never break a tool call on malformed input

session = str(data.get("session_id", ""))
digest = hashlib.sha1(session.encode()).hexdigest()
sentinel = os.path.join("/tmp", "claude-graph-used-" + digest)
armed_cache = os.path.join("/tmp", "claude-graph-armed-" + digest)

if MODE == "mark":
    try:
        open(sentinel, "w").close()
    except Exception:
        pass  # best-effort; worst case the gate asks for one more graph call
    sys.exit(0)

if os.environ.get("CLAUDE_SKIP_GRAPH_GATE"):
    sys.exit(0)

if os.path.exists(sentinel):
    sys.exit(0)

# Bash reaches this hook via an `if` filter selecting grep-like commands. Verify
# that independently: a shell command is only gated when it actually runs a
# whole-tree text search.
if str(data.get("tool_name", "")) == "Bash":
    command = str(data.get("tool_input", {}).get("command", ""))
    if not re.search(r"(^|[;&|(]|\s)(grep|egrep|fgrep|rg|ag|ack)(\s|$)", command):
        sys.exit(0)


def graph_exists_here():
    """True only when this repo has a non-empty graph. Any doubt returns False."""
    try:
        result = subprocess.run(
            ["code-review-graph", "status"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return False  # binary missing, hung, or unrunnable -> do not gate
    match = re.search(r"^Nodes:\s*(\d+)", result.stdout, re.MULTILINE)
    return bool(match) and int(match.group(1)) > 0


try:
    armed = open(armed_cache).read().strip() == "1"
except Exception:
    armed = graph_exists_here()
    try:
        with open(armed_cache, "w") as handle:
            handle.write("1" if armed else "0")
    except Exception:
        pass  # uncached means one extra status call, not a wrong answer

if not armed:
    sys.exit(0)

reason = (
    "Query the knowledge graph before text search (CLAUDE.md > MCP Tools: "
    "code-review-graph). No code-review-graph tool has been called this session.\n\n"
    "Use one of these first — they are faster and far cheaper than scanning files:\n"
    "  query_graph(pattern='file_summary', target='<path>')  — every symbol in a file, with line ranges\n"
    "  query_graph(pattern='callers_of'|'callees_of'|'tests_for', target='<symbol>')\n"
    "  semantic_search_nodes(query='<keyword>')              — find a symbol by name/meaning\n"
    "  get_impact_radius()                                   — blast radius of a change\n\n"
    "Any one graph call unlocks Grep/Glob for the rest of this session. If the "
    "graph genuinely does not cover what you need (markdown, fixtures, logs, or a "
    "stale graph), make the call anyway to confirm, then fall back to text search "
    "as the rule allows.\n\n"
    "If the code-review-graph MCP server is unavailable this session, no graph "
    "call can succeed and this gate cannot be satisfied. Say so and ask the user "
    "to restart with CLAUDE_SKIP_GRAPH_GATE=1 (or run `/hooks` to disable it) "
    "rather than working around it silently."
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
