#!/bin/bash

HOOK_DESC="GPG pinentry-mac integration"
HOOK_ROLES="all"

_find_pinentry_mac() {
  local gpgsuite_path="/usr/local/MacGPG2/libexec/pinentry-mac.app/Contents/MacOS/pinentry-mac"
  if [ -x "$gpgsuite_path" ]; then
    printf '%s' "$gpgsuite_path"
  else
    command -v pinentry-mac 2>/dev/null || true
  fi
}

hook_detect() {
  local config pinentry_path
  config="$HOME/.gnupg/gpg-agent.conf"
  pinentry_path="$(_find_pinentry_mac)"
  [ -n "$pinentry_path" ] || return 1
  [ -f "$config" ] || return 1
  grep -q "^pinentry-program $pinentry_path\$" "$config"
}

hook_install() {
  local config pinentry_path temp_file
  pinentry_path="$(_find_pinentry_mac)"
  [ -n "$pinentry_path" ] || return 1

  mkdir -p "$HOME/.gnupg"
  chmod 700 "$HOME/.gnupg" 2>/dev/null || true

  config="$HOME/.gnupg/gpg-agent.conf"
  temp_file="$(mktemp)"

  if [ -f "$config" ]; then
    awk '!/^pinentry-program[[:space:]]+/' "$config" >"$temp_file"
  fi
  printf '%s\n' "pinentry-program $pinentry_path" >>"$temp_file"
  mv "$temp_file" "$config"
  chmod 600 "$config" 2>/dev/null || true

  if command -v gpgconf >/dev/null 2>&1; then
    gpgconf --kill gpg-agent >/dev/null 2>&1 || true
    gpgconf --launch gpg-agent >/dev/null 2>&1 || true
  fi

  if command -v gpg-connect-agent >/dev/null 2>&1; then
    gpg-connect-agent updatestartuptty /bye >/dev/null 2>&1 || true
  fi

  return 0
}
