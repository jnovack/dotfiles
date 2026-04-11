#!/bin/bash

set -e

RAW_REPO_URL="${RAW_REPO_URL:-https://github.com/jnovack/dotfiles.git}"
BOOTSTRAP_REPO_DIR="${BOOTSTRAP_REPO_DIR:-$HOME/Source/dotfiles}"

if [ -f "${BASH_SOURCE[0]}" ] && [ -f "$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh" ]; then
  SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # shellcheck disable=SC1091
  . "$SCRIPT_DIR/lib/common.sh"
  # shellcheck disable=SC1091
  . "$SCRIPT_DIR/lib/packages.sh"
else
  printf '\n== Dotfiles Bootstrap ==\n'
  [ "$(uname -s)" = "Darwin" ] || {
    printf 'This installer currently supports macOS only.\n' >&2
    exit 1
  }

  if ! xcode-select -p >/dev/null 2>&1; then
    printf 'Xcode Command Line Tools are required. Launching installer now.\n'
    xcode-select --install >/dev/null 2>&1 || true
    printf 'Finish installing the command line tools, then rerun this command.\n'
    exit 1
  fi

  if ! command -v git >/dev/null 2>&1; then
    printf 'git is required but was not found after installing command line tools.\n' >&2
    exit 1
  fi

  mkdir -p "$HOME/Source"
  if [ -d "$BOOTSTRAP_REPO_DIR/.git" ]; then
    printf 'Refreshing dotfiles repo in %s\n' "$BOOTSTRAP_REPO_DIR"
    git -C "$BOOTSTRAP_REPO_DIR" pull --ff-only || printf 'Could not fast-forward the existing clone. Continuing with the local checkout.\n'
  else
    printf 'Cloning dotfiles repo into %s\n' "$BOOTSTRAP_REPO_DIR"
    git clone "$RAW_REPO_URL" "$BOOTSTRAP_REPO_DIR"
  fi

  exec "$BOOTSTRAP_REPO_DIR/install.sh" --local
fi

banner() {
  printf '\n%b' "$C_BOLD$C_MAGENTA"
  printf '  ____        _    _____ _ _           \n'
  printf ' |  _ \\  ___ | |_ |  ___(_) | ___  ___ \n'
  printf ' | | | |/ _ \\| __|| |_  | | |/ _ \\/ __|\n'
  printf ' | |_| | (_) | |_ |  _| | | |  __/\\__ \\\n'
  printf ' |____/ \\___/ \\__||_|   |_|_|\\___||___/\n'
  printf '%b\n' "$C_RESET"
}

clone_or_refresh_repo() {
  if [ -d "$DOTFILES_REPO/.git" ]; then
    step "Refreshing dotfiles repo"
    run_quiet git -C "$DOTFILES_REPO" pull --ff-only && ok "Repo is up to date." || warn "Could not fast-forward the repo automatically."
  else
    step "Cloning dotfiles repo"
    ensure_dir "$HOME/Source"
    run_quiet git clone "$RAW_REPO_URL" "$DOTFILES_REPO" && ok "Cloned repo into $DOTFILES_REPO." || die "Failed to clone the dotfiles repo."
  fi
}

install_oh_my_zsh() {
  if [ -d "$HOME/.oh-my-zsh" ]; then
    ok "oh-my-zsh already installed."
  else
    step "Installing oh-my-zsh"
    RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" >>"$DOTFILES_LAST_RUN_LOG" 2>&1 || die "oh-my-zsh installation failed."
    ok "Installed oh-my-zsh."
  fi
}

install_powerlevel10k() {
  local theme_dir
  theme_dir="$HOME/.oh-my-zsh/custom/themes/powerlevel10k"
  if [ -d "$theme_dir/.git" ]; then
    ok "powerlevel10k already installed."
  else
    step "Installing powerlevel10k"
    ensure_dir "$HOME/.oh-my-zsh/custom/themes"
    run_quiet git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$theme_dir" && ok "Installed powerlevel10k." || warn "Failed to install powerlevel10k."
  fi
}

install_meslo_nerd_font() {
  local brew cask
  cask="font-meslo-lg-nerd-font"
  brew="$(brew_bin 2>/dev/null || true)"
  [ -n "$brew" ] || return 0

  if "$brew" list --cask "$cask" >/dev/null 2>&1; then
    ok "Meslo Nerd Font already installed."
    return 0
  fi

  step "Installing Meslo Nerd Font for powerlevel10k"
  if run_quiet "$brew" install --cask "$cask"; then
    ok "Installed Meslo Nerd Font."
    return 0
  fi

  step "Ensuring Homebrew cask-fonts tap"
  run_quiet "$brew" tap homebrew/cask-fonts || true
  if run_quiet "$brew" install --cask "$cask"; then
    ok "Installed Meslo Nerd Font."
  else
    warn "Failed to install Meslo Nerd Font."
  fi
}

switch_to_zsh() {
  local zsh_path current_shell
  zsh_path="$(command -v zsh 2>/dev/null || true)"
  [ -n "$zsh_path" ] || return 0
  current_shell="$(dscl . -read "$HOME" UserShell 2>/dev/null | awk '{print $2}')"
  if [ "$current_shell" = "$zsh_path" ]; then
    ok "Login shell is already zsh."
    return 0
  fi

  step "Switching login shell to zsh"
  chsh -s "$zsh_path" >/dev/null 2>&1 && ok "Login shell updated to zsh." || warn "Unable to change login shell automatically."
}

install_packages_for_role() {
  local role="$1"
  local brew
  brew="$(brew_bin)"

  section "Packages"
  install_brew_list "$brew" formula "$SCRIPT_DIR/packages/formulas.txt"
  install_brew_list "$brew" cask "$SCRIPT_DIR/packages/casks.txt"
  install_brew_list "$brew" formula "$SCRIPT_DIR/packages/roles/$role.formulas.txt"
  install_brew_list "$brew" cask "$SCRIPT_DIR/packages/roles/$role.casks.txt"
  run_custom_hooks "$SCRIPT_DIR" "$role"
}

show_summary() {
  section "Summary"
  say "${C_DIM}Log file:${C_RESET} $DOTFILES_LAST_RUN_LOG"
  say "${C_DIM}Repo:${C_RESET} $DOTFILES_REPO"
  say "${C_DIM}Role:${C_RESET} $(load_role 2>/dev/null || printf 'personal')"
  say "${C_DIM}Next steps:${C_RESET}"
  say "  1. Review ~/.zshrc.local and ~/.gitconfig.local for machine-specific additions."
  say "  2. Run ./audit.sh on older machines before syncing."
  say "  3. Open a new terminal to load the canonical zsh config."
}

main() {
  local role
  ensure_macos
  banner
  section "System"
  ensure_xcode_clt
  ensure_homebrew
  clone_or_refresh_repo
  role="$(prompt_role)"
  install_packages_for_role "$role"

  section "Shell"
  install_oh_my_zsh
  install_powerlevel10k
  install_meslo_nerd_font
  switch_to_zsh

  section "Sync"
  "$SCRIPT_DIR/sync.sh"

  show_summary
}

main "$@"
