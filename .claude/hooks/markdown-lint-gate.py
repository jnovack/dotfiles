#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit): lint the written .md file, report failures.

Enforces CLAUDE.md > Markdown Lint Rules. A failing lint run in the turn it
happens teaches more than an always-on list of rules, so this lets that
template stay short.

Design choices (the failure modes a naive change would reintroduce):
  * Fails OPEN. No linter installed, a timeout, or bad input exits 0 silently;
    a missing tool must never block writing files.
  * Lints the WHOLE file, not the edited hunk: the rule is "fix all warnings in
    any file touched, including pre-existing ones".
  * Runs from the file's git root with a relative path, so the repo's own
    .markdownlint* config applies (e.g. a repo that relaxes MD013).
  * Skips paths that are not shipped documentation: `.local/` tracking files
    (MD024 fires there by construction), Claude memory and plan files, and
    temp/scratch files. Linting those burns turns on unfixable noise.
  * Prefers markdownlint-cli2 on PATH, then the npx cache (--no-install, so
    it never downloads anything mid-turn).
"""
import json
import os
import shutil
import subprocess
import sys

SKIP_PARTS = (
    "/.local/",
    "/.claude/projects/",
    "/.claude/plans/",
    "/tmp/",
    "/private/var/folders/",
)
MAX_LINES = 30


def linter():
    exe = shutil.which("markdownlint-cli2")
    if exe:
        return [exe]
    if shutil.which("npx"):
        return ["npx", "--no-install", "markdownlint-cli2"]
    return None


def git_root(directory):
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory, capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return directory
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else directory


def main():
    try:
        data = json.load(sys.stdin)
        path = (data.get("tool_input") or {}).get("file_path") or ""
    except Exception:
        return
    if not path.endswith(".md") or not os.path.isfile(path):
        return
    real = os.path.realpath(path)
    if any(part in real for part in SKIP_PARTS) or any(part in path for part in SKIP_PARTS):
        return
    cmd = linter()
    if not cmd:
        return
    root = git_root(os.path.dirname(real))
    rel = os.path.relpath(real, root)
    try:
        proc = subprocess.run(
            cmd + [rel], cwd=root, capture_output=True, text=True, timeout=25,
        )
    except Exception:
        return
    if proc.returncode == 0:
        return
    # cli2 prints findings on stderr as "file:line[:col] rule description".
    findings = [
        line for line in (proc.stderr + proc.stdout).splitlines()
        if line.startswith(rel + ":")
    ]
    if not findings:
        return  # linter error rather than lint findings; fail open
    shown = findings[:MAX_LINES]
    more = len(findings) - len(shown)
    reason = (
        f"markdownlint found {len(findings)} issue(s) in {path} "
        "(Markdown Lint Rules: fix all of them, including pre-existing ones):\n"
        + "\n".join(shown)
        + (f"\n... and {more} more" if more > 0 else "")
    )
    # PostToolUse "block" does not undo the write; it feeds `reason` back to
    # Claude so the fix happens in the same turn.
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
    sys.exit(0)
