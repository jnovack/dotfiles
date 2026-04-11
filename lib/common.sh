#!/bin/bash

set -u

DOTFILES_REPO="${DOTFILES_REPO:-$HOME/Source/dotfiles}"
DOTFILES_STATE_DIR="${DOTFILES_STATE_DIR:-$HOME/.config/dotfiles}"
DOTFILES_LOG_DIR="${DOTFILES_LOG_DIR:-$HOME/Library/Logs/dotfiles}"
DOTFILES_ROLE_FILE="${DOTFILES_ROLE_FILE:-$DOTFILES_STATE_DIR/role}"
DOTFILES_LAST_RUN_LOG="${DOTFILES_LAST_RUN_LOG:-$DOTFILES_LOG_DIR/run.log}"

mkdir -p "$DOTFILES_STATE_DIR" "$DOTFILES_LOG_DIR"

if [ -t 1 ]; then
  C_RESET="$(printf '\033[0m')"
  C_BOLD="$(printf '\033[1m')"
  C_DIM="$(printf '\033[2m')"
  C_RED="$(printf '\033[31m')"
  C_GREEN="$(printf '\033[32m')"
  C_YELLOW="$(printf '\033[33m')"
  C_BLUE="$(printf '\033[34m')"
  C_MAGENTA="$(printf '\033[35m')"
  C_CYAN="$(printf '\033[36m')"
else
  C_RESET=""
  C_BOLD=""
  C_DIM=""
  C_RED=""
  C_GREEN=""
  C_YELLOW=""
  C_BLUE=""
  C_MAGENTA=""
  C_CYAN=""
fi

log_line() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$DOTFILES_LAST_RUN_LOG"
}

say() {
  printf '%b\n' "$*"
  log_line "$*"
}

section() {
  printf '\n%b%s%b\n' "$C_BOLD$C_CYAN" "== $* ==" "$C_RESET"
  log_line "== $* =="
}

step() {
  printf '%b%s%b %s\n' "$C_BOLD$C_BLUE" "→" "$C_RESET" "$*"
  log_line "STEP $*"
}

ok() {
  printf '%b%s%b %s\n' "$C_GREEN" "✓" "$C_RESET" "$*"
  log_line "OK $*"
}

warn() {
  printf '%b%s%b %s\n' "$C_YELLOW" "!" "$C_RESET" "$*"
  log_line "WARN $*"
}

err() {
  printf '%b%s%b %s\n' "$C_RED" "✗" "$C_RESET" "$*"
  log_line "ERR $*"
}

die() {
  err "$*"
  exit 1
}

repo_root() {
  local script_dir
  script_dir="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  printf '%s\n' "$script_dir"
}

ensure_macos() {
  [ "$(uname -s)" = "Darwin" ] || die "This installer currently supports macOS only."
}

brew_bin() {
  if [ -x /opt/homebrew/bin/brew ]; then
    printf '%s\n' "/opt/homebrew/bin/brew"
    return 0
  fi
  if [ -x /usr/local/bin/brew ]; then
    printf '%s\n' "/usr/local/bin/brew"
    return 0
  fi
  if command -v brew >/dev/null 2>&1; then
    command -v brew
    return 0
  fi
  return 1
}

ensure_xcode_clt() {
  if xcode-select -p >/dev/null 2>&1; then
    ok "Xcode Command Line Tools already installed."
    return 0
  fi

  warn "Xcode Command Line Tools are required. Launching installer."
  xcode-select --install >/dev/null 2>&1 || true
  die "Finish the Xcode Command Line Tools installation, then rerun install.sh."
}

ensure_homebrew() {
  if brew_bin >/dev/null 2>&1; then
    ok "Homebrew already installed."
    return 0
  fi

  step "Installing Homebrew"
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >>"$DOTFILES_LAST_RUN_LOG" 2>&1 || die "Homebrew installation failed."
  ok "Installed Homebrew."
}

run_quiet() {
  "$@" >>"$DOTFILES_LAST_RUN_LOG" 2>&1
}

ensure_dir() {
  [ -d "$1" ] || mkdir -p "$1"
}

load_role() {
  if [ -n "${DOTFILES_ROLE:-}" ]; then
    printf '%s\n' "$DOTFILES_ROLE"
    return 0
  fi
  if [ -f "$DOTFILES_ROLE_FILE" ]; then
    cat "$DOTFILES_ROLE_FILE"
    return 0
  fi
  return 1
}

prompt_role() {
  local answer role
  role="$(load_role 2>/dev/null || true)"
  if [ -n "$role" ]; then
    printf '%s\n' "$role"
    return 0
  fi

  printf '\n%bSelect this machine role%b\n' "$C_BOLD" "$C_RESET"
  printf '  1. personal\n'
  printf '  2. work\n'
  printf '  3. pairing-host\n'
  printf 'Enter choice [1-3, default 1]: '
  read -r answer
  case "$answer" in
    2) role="work" ;;
    3) role="pairing-host" ;;
    *) role="personal" ;;
  esac
  printf '%s\n' "$role" >"$DOTFILES_ROLE_FILE"
  log_line "OK Saved machine role as $role."
  printf '%b%s%b %s\n' "$C_GREEN" "✓" "$C_RESET" "Saved machine role as $role." >&2
  printf '%s\n' "$role"
}

ensure_local_stub() {
  local target="$1"
  local content="$2"
  if [ -f "$target" ]; then
    ok "Local file already exists: $target"
    return 0
  fi

  printf '%s\n' "$content" >"$target"
  ok "Created local file stub: $target"
}

is_same_file() {
  local left="$1"
  local right="$2"
  [ -e "$left" ] && [ -e "$right" ] && cmp -s "$left" "$right"
}

show_diff() {
  local existing="$1"
  local canonical="$2"
  if command -v diff >/dev/null 2>&1; then
    diff -u "$existing" "$canonical" || true
  else
    warn "diff is unavailable, cannot show detailed changes."
  fi
}
