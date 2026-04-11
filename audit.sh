#!/bin/bash

set -e

SCRIPT_DIR="$(cd -P "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/common.sh"
# shellcheck disable=SC1091
. "$SCRIPT_DIR/lib/packages.sh"

section "Dotfiles Audit"

audit_target() {
  local rel="$1"
  local canonical="$SCRIPT_DIR/$rel"
  local target="$HOME/$rel"
  local local_file="$HOME/${rel}.local"

  step "Inspecting $rel"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$canonical" ]; then
    ok "$target is already symlinked to the canonical repo file."
  elif [ -f "$target" ]; then
    warn "$target exists as a regular file and should be reviewed before syncing."
    show_diff "$target" "$canonical"
    warn "Shared changes should move into $canonical."
    warn "Machine-specific changes should move into $local_file."
  else
    warn "$target is missing."
  fi

  if [ -f "$local_file" ]; then
    ok "$local_file exists for local-only additions."
  else
    warn "$local_file does not exist yet."
  fi
}

audit_brew() {
  local brew formulas casks expected extra missing item
  if ! brew="$(brew_bin)"; then
    warn "Homebrew is not installed, skipping package audit."
    return 0
  fi

  section "Package Audit"
  formulas="$(mktemp)"
  casks="$(mktemp)"
  expected="$(mktemp)"
  extra="$(mktemp)"
  missing="$(mktemp)"

  "$brew" list --formula | sort >"$formulas"
  "$brew" list --cask | sort >"$casks"

  {
    package_file_lines "$SCRIPT_DIR/packages/formulas.txt"
    package_file_lines "$SCRIPT_DIR/packages/roles/$(load_role 2>/dev/null || printf 'personal').formulas.txt"
  } | sort -u >"$expected"

  step "Shared and role-based formulas expected on this machine"
  cat "$expected"

  if comm -23 "$expected" "$formulas" >"$missing" && [ -s "$missing" ]; then
    warn "Missing formulas:"
    cat "$missing"
  else
    ok "No expected formulas are missing."
  fi

  if comm -13 "$expected" "$formulas" >"$extra" && [ -s "$extra" ]; then
    warn "Extra formulas installed outside the registry:"
    cat "$extra"
    warn "Review these and decide whether to add them to packages/ or remove them."
  else
    ok "No formula drift detected beyond the registry."
  fi

  {
    package_file_lines "$SCRIPT_DIR/packages/casks.txt"
    package_file_lines "$SCRIPT_DIR/packages/roles/$(load_role 2>/dev/null || printf 'personal').casks.txt"
  } | sort -u >"$expected"

  step "Shared and role-based casks expected on this machine"
  cat "$expected"

  if comm -23 "$expected" "$casks" >"$missing" && [ -s "$missing" ]; then
    warn "Missing casks:"
    cat "$missing"
  else
    ok "No expected casks are missing."
  fi

  if comm -13 "$expected" "$casks" >"$extra" && [ -s "$extra" ]; then
    warn "Extra casks installed outside the registry:"
    cat "$extra"
    warn "Review these and decide whether to add them to packages/ or remove them."
  else
    ok "No cask drift detected beyond the registry."
  fi

  rm -f "$formulas" "$casks" "$expected" "$extra" "$missing"
}

section "Shell and Git"
audit_target ".zshrc"
audit_target ".gitconfig"

step "Inspecting shell tooling"
if [ -d "$HOME/.oh-my-zsh" ]; then
  ok "oh-my-zsh is installed."
else
  warn "oh-my-zsh is not installed."
fi

if [ -d "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" ]; then
  ok "powerlevel10k is installed."
else
  warn "powerlevel10k is not installed."
fi

if [ "$SHELL" = "$(command -v zsh 2>/dev/null)" ]; then
  ok "zsh is the active login shell."
else
  warn "Current login shell is $SHELL. Consider switching to zsh."
fi

audit_brew
