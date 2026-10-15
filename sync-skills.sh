#!/bin/bash

set -e

SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"

# Keep the existing Codex location; override the destination for other setups.
SKILLS_DIR="${DOTFILES_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"

section "Codex Skills Sync"
ensure_dir "$SKILLS_DIR"

sync_skill() {
  local source_dir="$1"
  local name target_dir backup_dir
  name="$(basename "$source_dir")"
  target_dir="$SKILLS_DIR/$name"

  step "Syncing skill $name"

  if [ -L "$target_dir" ]; then
    if [ "$(readlink "$target_dir")" = "$source_dir" ]; then
      ok "$target_dir already points to the canonical skill."
      return 0
    fi
    err "Refusing to replace existing skill symlink: $target_dir"
    return 1
  fi

  if [ -e "$target_dir" ]; then
    if [ ! -d "$target_dir" ] || ! diff -qr "$target_dir" "$source_dir"; then
      err "Refusing to replace $target_dir because it differs from the canonical skill."
      warn "Reconcile local edits with $source_dir before retrying."
      return 1
    fi

    # Back up identical copies outside the discovery directory before linking,
    # so local work is preserved without creating duplicate skill entries.
    backup_dir="$(mktemp -d "$SKILLS_DIR/../skill-backup.XXXXXX")" || return 1
    mv "$target_dir" "$backup_dir/$name" || return 1
    ok "Preserved original skill in $backup_dir/$name"
    if ! ln -s "$source_dir" "$target_dir"; then
      mv "$backup_dir/$name" "$target_dir"
      return 1
    fi
  else
    ln -s "$source_dir" "$target_dir" || return 1
  fi
  ok "Linked $target_dir -> $source_dir"
}

status=0
for skill_dir in "$SCRIPT_DIR"/.codex/skills/*; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  sync_skill "$skill_dir" || status=1
done

exit "$status"
