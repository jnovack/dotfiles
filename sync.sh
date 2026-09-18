#!/bin/bash

set -e

SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

CANONICAL_FILES="
.zshrc
.gitconfig
.p10k.zsh
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

  if [ -L "$target_file" ] && [ "$(readlink "$target_file")" = "$source_file" ]; then
    ok "$target_file already points to the canonical file."
    return 0
  fi

  if [ -e "$target_file" ] && ! is_same_file "$target_file" "$source_file"; then
    err "Refusing to replace $target_file because it differs from the canonical repo file."
    warn "Move machine-specific changes into $(local_companion "$rel") before retrying."
    show_diff "$target_file" "$source_file"
    return 1
  fi

  rm -f "$target_file"
  ln -s "$source_file" "$target_file"
  ok "Linked $target_file -> $source_file"
}

status=0
for file in $CANONICAL_FILES; do
  sync_file "$file" || status=1
done

exit "$status"
