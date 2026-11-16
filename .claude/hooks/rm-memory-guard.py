#!/usr/bin/env python3
"""PreToolUse gate: confirm before deleting a file this repo's memory (or memory naming this repo) references.

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
  * Scopes hits to the deleted file's repo. On 2026-11-10 meal-ticket's memory
    mentioned `.local/REVIEW.md` and denied dotfiles' routine `rm .local/REVIEW.md`:
    generic tracking names recur across unrelated repos' memories. A memory line
    counts only when its project dir is an ancestor of the target (compared by
    encoded-name EQUALITY, never prefix, so `-...-meal` is not `-...-meal-ticket`),
    or lies inside the target's repo (encoded name starts with the encoded root
    plus `-`: a session started in `repo/cmd` keeps guarding `repo/.local/PLAN.md`;
    a sibling repo whose name extends this one's also matches, which over-guards,
    the safe direction), or when the line names `<repo dir>/<path>` (e.g.
    `dotfiles/.local/TODO.md`), which keeps genuine cross-repo references. A line
    naming only `.local/TODO.md` does not. Scoping falls back to the old global
    basename match when it cannot be trusted: no `.git` ancestor (e.g.
    `~/.claude/plans/x.md`); a target the shell expands (`$VAR`, `$(…)`, a backtick
    or a glob); or a `cd`/`pushd` segment, even behind `{`, `then` or `do`, after
    which the target is not relative to the payload `cwd`. The fallback
    over-guards rather than under-guards.
  * Guards glob targets. `rm .local/PLAN*.md` is an ordinary way to delete the only
    copy, and a raw `PLAN*.md` never substring-matches a memory line. With a known
    `cwd`, no prior `cd`/`pushd` and no `$`/backtick in the token, the glob is
    expanded against `cwd` and each match is checked as a literal target (same
    repo scoping, same report exemption, `MIN_TOKEN_LEN` per basename). Otherwise,
    or when nothing matches, the basename pattern is `fnmatch`ed globally against
    each word of each memory line (a word is split at whitespace, backticks and
    quotes, then reduced to its basename): over-guards, the safe direction. An
    unresolved shell expression is never globbed. Lexical guard only: names built
    dynamically are not guaranteed.
  * Splits segments with a quote-aware raw scanner (`segments()`), not a regex.
    A regex split before `shlex` cut `grep -E 'a|rm .local/PLAN.md b'` at the quoted
    `|`; the fragment's unbalanced quote fell back to whitespace splitting, `rm`
    became the leader and the hook denied a harmless grep. The scanner keeps quotes
    raw until real operator boundaries are known and only then tokenizes, because
    after `shlex` `';'` and `;` are indistinguishable. It is not a shell parser: no
    substitution traversal, nothing is evaluated. Unbalanced quotes fall back to
    the old regex split (guarding beats silently allowing).
  * Compares ancestors of both abspath and realpath. Which form Claude Code
    recorded in the project dir name is unknown, and they differ for macOS temp
    dirs (`/var` vs `/private/var`) and symlinked dirs. The repo-root walk uses
    the abspath only, so a target reached through a symlink into a repo (e.g.
    `~/.claude/hooks/x.py`) finds no `.git` and takes the global match.
  * Exempts `.local/REVIEW.md`, `.local/REVIEW.<NAME>.md` and `.local/ASSESSMENT.md`.
    They are regenerated punch-lists that `/todo-next`, `/todo-checkpoint`,
    `/refactor-next` and `/refactor-checkpoint` delete by design; guarding them
    stalls the unattended loops on a deny that needs a human. `TODO.md`,
    `REFACTOR*.md`, `COMMIT-MSG.txt` and `PLAN.md` are scoped, not exempt.
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
import fnmatch
import glob
import json
import os
import re
import shlex
import sys

MAX_HITS_SHOWN = 6
MIN_TOKEN_LEN = 4
# Regenerated `.local/` punch-lists; see the exemption bullet in the docstring.
EXEMPT_REPORT = re.compile(r"^(REVIEW(\.[A-Za-z0-9_-]+)?|ASSESSMENT)\.md$")


def encode(path):
    """Claude Code's project-dir naming: every non-alphanumeric becomes `-`."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def scope_for(token, cwd):
    """Return (encoded ancestor dirs, repo-relative suffix), or None for global.

    None means scoping cannot be trusted (no repo root, or any error), so the
    candidate keeps today's global basename match. Over-guards, never under-guards.
    """
    # `$REPOB/x`, `$(pwd)/x`, a backtick or a glob is expanded by the shell, not
    # here; joined to cwd it would scope the delete to the wrong repo and allow
    # it. Unknown target, so global.
    if any(char in token for char in "$`*?["):
        return None
    try:
        path = os.path.expanduser(token)
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        absolute = os.path.abspath(path)
        real = os.path.realpath(path)
        root = None
        current = os.path.dirname(absolute)
        while True:
            if os.path.exists(os.path.join(current, ".git")):
                root = current
                break
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        if root is None:
            return None
        ancestors = set()
        for form in (absolute, real):
            current = os.path.dirname(form)
            while True:
                ancestors.add(encode(current))
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
        # Encoded root + "-": a project dir inside the repo (a session started in
        # `repo/cmd`) is the repo's own memory too.
        inside = {encode(root) + "-", encode(os.path.realpath(root)) + "-"}
        return ancestors, os.path.relpath(absolute, os.path.dirname(root)), inside
    except Exception:
        return None


def split_tokens(span):
    try:
        return shlex.split(span)
    except Exception:
        return span.split()  # e.g. a trailing backslash


def segments(command):
    """Yield one token list per simple command, splitting only on real operators.

    Scans the RAW text so quoted/escaped `;` `|` `&` and newlines stay argument
    data. `&` belonging to a redirect (`2>&1`, `>&2`, `&>`) is kept. Parentheses
    stay in the span (`(rm x)`, `$(pwd)/x` are handled by the caller). A `#` at a
    word start is a comment through its newline, which still ends the command.
    Backslash-newline is a continuation. Raises ValueError on unbalanced quotes.
    """
    spans = []
    buf = []
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if ch == "\\":
            if command[i + 1:i + 2] != "\n":  # escaped newline: dropped entirely
                buf.append(command[i:i + 2])
            i += 2
        elif ch == "'":
            end = command.find("'", i + 1)
            if end < 0:
                raise ValueError("unbalanced single quote")
            buf.append(command[i:end + 1])
            i = end + 1
        elif ch == '"':
            buf.append(ch)
            i += 1
            while True:
                if i >= n:
                    raise ValueError("unbalanced double quote")
                c = command[i]
                if c == "\\" and i + 1 < n:
                    if command[i + 1] != "\n":
                        buf.append(command[i:i + 2] if command[i + 1] in '$`"\\' else c)
                        i += 2 if command[i + 1] in '$`"\\' else 1
                    else:
                        i += 2
                    continue
                buf.append(c)
                i += 1
                if c == '"':
                    break
        # Compare whole buffered chunks, not their last character: an escape is
        # buffered as one 2-char chunk, so `a\ #x` keeps `#` as data and `a\>&`
        # is `a>` then a real `&`. Testing `[-1:]` swallowed the next command.
        elif ch == "#" and (not buf or (len(buf[-1]) == 1 and buf[-1].isspace())):
            while i < n and command[i] != "\n":
                i += 1
        elif ch in ";|\n" or (
            ch == "&"
            and not (buf and buf[-1] in ("<", ">"))
            and command[i + 1:i + 2] != ">"
        ):
            spans.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(ch)
            i += 1
    spans.append("".join(buf))
    return [split_tokens(span) for span in spans]


def legacy_segments(command):
    # Quote-unaware split, kept only for commands the scanner rejects (unbalanced
    # quotes): the fragments still reach the whitespace fallback and get guarded.
    return [split_tokens(part) for part in re.split(r"&&|\|\||[;&|\n]", command)]


def command_segments(command):
    try:
        return segments(command)
    except Exception:
        return legacy_segments(command)


def memory_words(line):
    """Basenames of the words in a memory line, for glob-pattern fallback."""
    words = set()
    for raw in re.split(r"[\s`'\"]+", line):
        word = raw.lstrip("([{<").rstrip(".,;:!?)]}>")
        if word:
            words.add(os.path.basename(word.rstrip("/")))
    return words


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open

command = str(data.get("tool_input", {}).get("command", ""))
if not command or not re.search(r"(^|[;&|(]|\s)rm(\s|$)", command):
    sys.exit(0)

# Split on shell operators FIRST (outside quotes; see `segments()`), then tokenize
# each segment. shlex.split does not treat `;` `&&` `|` as operators — it returns
# "b.py;" as a single token — so scanning its output for separator tokens never
# resets and every word of a chained `echo`/`ls`/`jq` is read as an rm argument.
# That produced a false positive on the very command installing this hook.
PREFIXES = {"sudo", "command", "time", "xargs", "env", "nohup"}
# Words that can lead a segment before its command: `{ cd B; rm x; }` splits to
# `{ cd B`, and `if …; then cd B; rm x` to `then cd B`. Skipping only PREFIXES
# missed those `cd`s, so the rm was scoped to the payload cwd and allowed.
LEADERS = {"{", "(", "!", "then", "do", "else", "elif", "if", "while", "until"}

try:
    cwd = str(data.get("cwd") or os.getcwd())
except Exception:
    cwd = ""  # deleted process cwd: relative targets then fail scoping -> global
moved = False  # a cd/pushd segment seen: later targets are not relative to cwd
candidates = {}  # basename -> [scope, ...]; a list so two repos' same name both count
# Glob basename -> True when every use sat under `.local/`. Fallback patterns are
# matched globally against memory words; a `.local/` one skips report names the
# literal delete would exempt, or the loops' `rm -f .local/REVIEW*.md` (no report
# present, nothing to expand) denies on any memory mentioning `REVIEW.md`.
patterns = {}
for tokens in command_segments(command):
    index = 0
    word = ""
    while index < len(tokens):
        word = tokens[index].lstrip("({")  # `(cd` / `(rm` arrive as one token
        if word and word not in LEADERS and word not in PREFIXES:
            break
        index += 1
    if word in {"cd", "pushd"}:
        moved = True
        continue
    if index >= len(tokens) or os.path.basename(word) != "rm":
        continue  # this segment does not invoke rm
    for token in tokens[index + 1:]:
        if token.startswith("-"):
            continue
        # The segment split leaves a subshell's closing paren attached.
        token = token.rstrip(")}")
        base = os.path.basename(token.rstrip("/"))
        try:
            parent = os.path.basename(
                os.path.dirname(os.path.abspath(os.path.join(cwd, os.path.expanduser(token.rstrip("/")))))
            )
        except Exception:
            parent = ""
        if re.match(r"^(\d*[<>]|&>)", token):
            continue  # redirect word (`2>&1`, `&>log`), not a delete target
        if any(char in token for char in "*?["):
            # Glob: expand only where the result is trustworthy; the literal
            # basename below is still kept so a quoted name that really contains
            # glob characters keeps matching.
            matches = []
            if cwd and not moved and not any(char in token for char in "$`"):
                try:
                    matches = glob.glob(os.path.join(cwd, os.path.expanduser(token.rstrip("/"))))
                except Exception:
                    matches = []
            for match in matches:
                match_base = os.path.basename(match)
                match_parent = os.path.basename(os.path.dirname(os.path.abspath(match)))
                if EXEMPT_REPORT.match(match_base) and match_parent == ".local":
                    continue
                if len(match_base) >= MIN_TOKEN_LEN:
                    candidates.setdefault(match_base, []).append(scope_for(match, cwd))
            if not matches and len(base) >= MIN_TOKEN_LEN:
                patterns[base] = patterns.get(base, True) and parent == ".local"
        if EXEMPT_REPORT.match(base) and parent == ".local":
            continue
        if len(base) >= MIN_TOKEN_LEN:
            candidates.setdefault(base, []).append(None if moved else scope_for(token, cwd))

if not candidates and not patterns:
    sys.exit(0)

hits = []
for memory_file in sorted(glob.glob(os.path.expanduser("~/.claude/projects/*/memory/*.md"))):
    try:
        with open(memory_file, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except Exception:
        continue
    name = os.path.basename(memory_file)
    project = encode(os.path.basename(os.path.dirname(os.path.dirname(memory_file))))
    for line in lines:
        if patterns and any(
            fnmatch.fnmatchcase(word, pattern) and not (local and EXEMPT_REPORT.match(word))
            for pattern, local in patterns.items()
            for word in memory_words(line)
        ):
            hits.append("  [{}] {}".format(name, line.strip()[:160]))
            if len(hits) >= MAX_HITS_SHOWN * 4:
                break
            continue  # one hit per line
        for candidate, scopes in candidates.items():
            if candidate in line and any(
                scope is None
                or project in scope[0]
                or any(project.startswith(prefix) for prefix in scope[2])
                or scope[1] in line
                for scope in scopes
            ):
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
