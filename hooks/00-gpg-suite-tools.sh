#!/bin/bash

HOOK_DESC="GPG Suite tools"
HOOK_ROLES="all"

hook_detect() {
  local gpgsuite_pinentry
  gpgsuite_pinentry="/usr/local/MacGPG2/libexec/pinentry-mac.app/Contents/MacOS/pinentry-mac"
  [ -x "$gpgsuite_pinentry" ] || command -v pinentry-mac >/dev/null 2>&1
}

hook_install() {
  run_quiet "$(brew_bin)" install --cask gpg-suite-no-mail
}
