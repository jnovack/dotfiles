#!/bin/bash

set -e

SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

CANONICAL_FILES="
.zshrc
.gitconfig
.p10k.zsh
.tmux.conf
"

# Directories under ~/.claude that point back into this repo. The hook commands
# in settings.json run $HOME/.claude/hooks/*, so a machine without these links
# has broken hooks and no loop helpers. ~/.claude/CLAUDE.md is deliberately not
# listed: claude-templates assemble generates it. .claude/docs, templates and
# PLAN.templating-machine.md are left out because nothing loads them from ~/.claude.
CANONICAL_DIRS="
.claude/bin
.claude/commands
.claude/hooks
.claude/skills
"

section "Dotfiles Sync"

ensure_dir "$HOME/.config"
ensure_local_stub "$HOME/.zshrc.local" "# Machine-local zsh additions live here."
ensure_local_stub "$HOME/.gitconfig.local" "# Machine-local git settings live here."
ensure_local_stub "$HOME/.p10k.local.zsh" "# Machine-local p10k additions live here."

# Name the machine-local companion a canonical file actually sources. Appending
# ".local" is right for .zshrc and .gitconfig but not for .p10k.zsh, whose
# companion is .p10k.local.zsh -- the suffix has to land before the extension so
# zsh still sees a .zsh file. Keep this in step with the ensure_local_stub calls
# above; a wrong name here sends someone to edit a file nothing reads.
local_companion() {
  case "$1" in
    .p10k.zsh) printf '%s\n' "$HOME/.p10k.local.zsh" ;;
    *)         printf '%s\n' "$HOME/$1.local" ;;
  esac
}

sync_file() {
  local rel="$1"
  local source_file="$SCRIPT_DIR/$rel"
  local target_file="$HOME/$rel"

  step "Syncing $rel"

  # A missing source would otherwise fall into the file branch below and leave
  # a dangling link reported as "Linked" -- or, for an existing link to it, as
  # already canonical. Refuse before either can claim success.
  if [ ! -e "$source_file" ]; then
    err "Canonical source $source_file is missing; not linking $target_file."
    return 1
  fi

  if [ -L "$target_file" ] && [ "$(readlink "$target_file")" = "$source_file" ]; then
    ok "$target_file already points to the canonical file."
    return 0
  fi

  if [ -d "$source_file" ]; then
    # Test -L before -e: -e is false for a dangling symlink, which would fall
    # through to the rm -f below and silently replace a foreign link. A directory
    # has no .local companion, so give reconcile guidance instead of
    # local_companion advice or a diff.
    if [ -L "$target_file" ] || [ -e "$target_file" ]; then
      err "Refusing to replace $target_file because it is not the canonical link to $source_file."
      warn "Move or remove $target_file yourself, then rerun sync.sh."
      return 1
    fi
  elif [ -e "$target_file" ] && ! is_same_file "$target_file" "$source_file"; then
    err "Refusing to replace $target_file because it differs from the canonical repo file."
    warn "Move machine-specific changes into $(local_companion "$rel") before retrying."
    show_diff "$target_file" "$source_file"
    return 1
  fi

  # Callers run this as `sync_file ... || status=1`, which turns set -e off
  # inside the function, so a failed mkdir or ln would fall through to the
  # "Linked" line and return 0. Check each status explicitly.
  if ! ensure_dir "$(dirname "$target_file")"; then
    err "Cannot create $(dirname "$target_file") for $target_file."
    return 1
  fi

  rm -f "$target_file"
  if ! ln -s "$source_file" "$target_file"; then
    err "Failed to link $target_file -> $source_file"
    return 1
  fi
  ok "Linked $target_file -> $source_file"
}

status=0
for file in $CANONICAL_FILES; do
  sync_file "$file" || status=1
done
for dir in $CANONICAL_DIRS; do
  sync_file "$dir" || status=1
done

"$SCRIPT_DIR/sync-skills.sh" || status=1

exit "$status"
