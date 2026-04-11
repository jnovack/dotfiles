# Enable Powerlevel10k instant prompt. Keep this close to the top.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"

plugins=(
  git
  macos
  docker
  npm
  colorize
  cp
  docker-compose
  dotenv
  git-prompt
  golang
  grc
  history
  mosh
  rsync
  screen
  tmux
  vscode
)

if [[ -d "$ZSH" ]]; then
  source "$ZSH/oh-my-zsh.sh"
fi

autoload -U compinit && compinit

[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh
[[ -f ~/.iterm2_shell_integration.zsh ]] && source ~/.iterm2_shell_integration.zsh

export GPG_TTY="$(tty)"

alias generate-password="cat /dev/urandom | LC_CTYPE=C tr -dc '[:alnum:]' | fold -w 32 | head -n 4"
alias docker-config-decode="jq '.[].Spec.Data' | cut -d'\"' -f2 | base64 -d"

openssl-cert-check() {
  echo | \
    openssl s_client -servername "$1" -connect "${3:-${1}}:${2:-443}" 2>/dev/null | \
    openssl x509 -noout -text
}

openssl-key-match() {
  echo "${1}.key"
  openssl rsa -noout -modulus -in "${1}.key" 2>/dev/null | openssl md5
  echo "${1}.crt"
  openssl x509 -noout -modulus -in "${1}.crt" 2>/dev/null | openssl md5
}

dive() {
  if [[ -z "$(docker images -q wagoodman/dive:latest 2>/dev/null)" ]]; then
    docker pull wagoodman/dive:latest
  fi
  if [[ -z "$(docker images -q "$1" 2>/dev/null)" ]]; then
    docker pull "$1"
  fi

  docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest "$1"
}

ghcr-login() {
  [[ -f ~/.env ]] && source ~/.env
  echo "$GHCR_TOKEN" | docker login ghcr.io -u jnovack --password-stdin
}

cdroot() {
  local current_dir
  current_dir="$(pwd)"
  while [[ ! -d "$current_dir/.git" && "$current_dir" != "/" ]]; do
    current_dir="$(dirname "$current_dir")"
  done

  if [[ -d "$current_dir/.git" ]]; then
    cd "$current_dir" || return 1
  else
    echo "No .git directory found in the directory tree."
  fi
}

psync() {
  rsync -PLarvz -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "$@"
}

if [[ -n "$SSH_TTY" && -z "$TMUX" ]] && command -v tmux >/dev/null 2>&1; then
  tmux attach-session -t ssh_tmux || tmux new-session -s ssh_tmux
fi

export NVM_DIR="$HOME/.nvm"
[[ -s "$NVM_DIR/nvm.sh" ]] && . "$NVM_DIR/nvm.sh"
[[ -s "$NVM_DIR/bash_completion" ]] && . "$NVM_DIR/bash_completion"

if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

if command -v brew >/dev/null 2>&1; then
  [[ -s "$(brew --prefix)/etc/bash_completion.d/az" ]] && . "$(brew --prefix)/etc/bash_completion.d/az"
fi

export SDKROOT="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null)"

if [[ -f "$HOME/.zshrc.local" ]]; then
  source "$HOME/.zshrc.local"
fi
