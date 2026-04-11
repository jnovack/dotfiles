#!/bin/bash

set -e

SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

CANONICAL_FILES="
.zshrc
.gitconfig
"

section "Dotfiles Sync"

ensure_dir "$HOME/.config"
ensure_local_stub "$HOME/.zshrc.local" "# Machine-local zsh additions live here."
ensure_local_stub "$HOME/.gitconfig.local" "# Machine-local git settings live here."

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
    warn "Move machine-specific changes into ${target_file}.local before retrying."
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
