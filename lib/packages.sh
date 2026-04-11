#!/bin/bash

package_file_lines() {
  local file="$1"
  [ -f "$file" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="$(printf '%s' "$line" | sed 's/[[:space:]]*$//')"
    [ -n "$line" ] && printf '%s\n' "$line"
  done <"$file"
}

install_brew_list() {
  local brew="$1"
  local kind="$2"
  local file="$3"
  local item args

  package_file_lines "$file" | while IFS= read -r item; do
    [ -n "$item" ] || continue
    if [ "$kind" = "cask" ]; then
      args="--cask"
    else
      args=""
    fi

    if "$brew" list $args "$item" >/dev/null 2>&1; then
      ok "$item already installed."
    else
      step "Installing $item"
      if [ "$kind" = "cask" ]; then
        run_quiet "$brew" install --cask "$item" && ok "Installed $item." || warn "Failed to install $item."
      else
        run_quiet "$brew" install "$item" && ok "Installed $item." || warn "Failed to install $item."
      fi
    fi
  done
}

run_custom_hooks() {
  local repo="$1"
  local role="$2"
  local hook

  for hook in "$repo"/hooks/*.sh; do
    [ -f "$hook" ] || continue
    HOOK_DESC=""
    HOOK_ROLES="all"
    unset -f hook_detect hook_install 2>/dev/null || true
    # shellcheck disable=SC1090
    . "$hook"

    case "$HOOK_ROLES" in
      all|"$role"|*",$role,"*|"$role,"*|*",$role") ;;
      *) continue ;;
    esac

    if hook_detect; then
      ok "$HOOK_DESC already configured."
    else
      step "Running hook: $HOOK_DESC"
      if hook_install; then
        ok "$HOOK_DESC configured."
      else
        warn "$HOOK_DESC failed. See log for details."
      fi
    fi
  done
}
