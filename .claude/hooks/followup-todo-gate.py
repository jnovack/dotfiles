#!/usr/bin/env python3
"""Stop hook: block a final response that defers work without a TODO ID.

Enforces CLAUDE.md > Commitment Durability. Agents end turns with "Left for
you:" / "open decisions" / "worth a follow-up" lists that exist only in chat
and are lost with the session. This hook scans the turn's final assistant text
and, when a deferral phrase appears with no TODO ID nearby, sends Claude back
to file the item via `todo-add` and cite its ID.

Design choices (the failure modes a naive change would reintroduce):
  * Fails OPEN on every error path. A spurious block fights the user on
    unrelated turns, so bad JSON, an unreadable transcript, or anything else
    unexpected exits 0 silently.
  * Honors stop_hook_active, so the block resolves in one extra cycle instead
    of looping (Claude Code also force-stops after repeated blocks).
  * Skips SUBAGENTS. Claude Code fires Stop as SubagentStop inside a subagent;
    its output goes to the orchestrator, not the user, so the orchestrator's
    own final response is the one that must cite IDs.
  * Fires per TURN, not once per session (unlike intent-capture-nudge.py). A
    deferral lost on turn 9 is as lost as one on turn 1.
  * Matches per PARAGRAPH, with the next paragraph also counting, so a
    "Left for you:" heading followed by a bulleted list of IDs passes, while
    one cited ID elsewhere in a long summary does not excuse an untracked item.
  * Ignores fenced code, `>` blockquotes and inline quoted/backticked spans:
    quoting a rule, a summary or a trigger phrase is not deferring work, and
    all three fired in real transcripts.
"""
import json
import re
import sys

# Phrases that announce work is being deferred rather than done. Kept narrow on
# purpose: a bare "later" or "TODO" would fire on ordinary prose.
DEFERRAL = re.compile(
    r"left for you"
    r"|open (?:decision|question)s?\b"
    r"|follow[- ]?ups?\b"
    r"|\bfor later\b"
    r"|circl(?:e|ed|ing) back"
    r"|out of scope"
    r"|not (?:yet )?tracked"
    r"|\brevisit(?:ing)? (?:this|it|that|later)\b"
    r"|(?:separate|future|later) (?:pr|change|cleanup|clean-up|pass)\b",
    re.IGNORECASE,
)

# todo-add IDs: CATEGORY-DESCRIPTOR-## (descriptor may itself contain hyphens,
# e.g. DOCS-STALE-COUNT-01).
TODO_ID = re.compile(r"\b[A-Z]{2,8}(?:-[A-Z0-9]{1,10})+-\d{2,}\b")

FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
QUOTE = re.compile(r"^\s*>.*$", re.MULTILINE)
# Inline "quoted", “curly-quoted” or `code` spans name a phrase, they don't use
# it: summaries describing this hook listed its trigger words and blocked.
MENTION = re.compile(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`')


def final_text(data):
    """Return the turn's final assistant text, or "" if unavailable."""
    text = data.get("last_assistant_message")
    if isinstance(text, str):
        return text
    path = data.get("transcript_path")
    if not path:
        return ""
    with open(path, encoding="utf-8") as fh:
        entries = [json.loads(line) for line in fh if line.strip()]
    # One assistant message is written as several consecutive entries (one per
    # content block); collect text back to the last non-assistant entry.
    parts = []
    for entry in reversed(entries):
        if entry.get("type") != "assistant":
            if parts:
                break
            continue
        content = entry.get("message", {}).get("content", [])
        if isinstance(content, str):
            parts.append(content)
            continue
        for block in reversed(content):
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
    return "\n".join(reversed(parts))


def untracked(text):
    """Return paragraphs that defer work with no TODO ID in or after them."""
    prose = MENTION.sub("", QUOTE.sub("", FENCE.sub("", text)))
    paras = [p for p in re.split(r"\n\s*\n", prose) if p.strip()]
    hits = []
    for i, para in enumerate(paras):
        if not DEFERRAL.search(para):
            continue
        following = paras[i + 1] if i + 1 < len(paras) else ""
        if TODO_ID.search(para) or TODO_ID.search(following):
            continue
        hits.append(para.strip())
    return hits


def main():
    try:
        data = json.load(sys.stdin)
        if data.get("stop_hook_active"):
            return
        if data.get("agent_type") or data.get("agent_id"):
            return
        hits = untracked(final_text(data))
    except Exception:
        return  # fail-open
    if not hits:
        return

    quoted = "\n".join("> " + h.splitlines()[0][:160] for h in hits[:5])
    # The closing sentence is load-bearing: this text becomes Claude's next
    # instruction, so it must not read as "stop" or it truncates pending work.
    reason = (
        "Commitment Durability check: your response defers work without a TODO "
        "ID, so it will be lost when the session ends:\n"
        f"{quoted}\n"
        "For each real deferred item, add a row to .local/TODO.md with the "
        "todo-add skill, then restate the item with its ID (e.g. 'tracked as "
        "FIX-ESHOST-01'). If a match is not actually deferred work, say so in "
        "one line. Then resume any unfinished work from this turn."
    )
    # Top-level decision "block" is the documented Stop-hook shape: it prevents
    # the stop and feeds `reason` back to Claude as its next instruction.
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
    sys.exit(0)
