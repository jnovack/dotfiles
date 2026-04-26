# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Path to your oh-my-zsh installation.
export ZSH="/Users/jnovack/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/robbyrussell/oh-my-zsh/wiki/Themes
#ZSH_THEME="robbyrussell"
ZSH_THEME="powerlevel10k/powerlevel10k"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in ~/.oh-my-zsh/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to automatically update without prompting.
# DISABLE_UPDATE_PROMPT="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS=true

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in ~/.oh-my-zsh/plugins/*
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
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

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh
[[ -f ~/.p10k.local.zsh ]] && source ~/.p10k.local.zsh
[[ -f ~/.iterm2_shell_integration.zsh ]] && source ~/.iterm2_shell_integration.zsh

export GPG_TTY="$(tty)"
if command -v gpgconf >/dev/null 2>&1; then
  gpgconf --launch gpg-agent >/dev/null 2>&1 || true
fi
if command -v gpg-connect-agent >/dev/null 2>&1; then
  gpg-connect-agent updatestartuptty /bye >/dev/null 2>&1 || true
fi

alias generate-password="cat /dev/urandom | LC_CTYPE=C tr -dc '[:alnum:]' | fold -w 32 | head -n 4"

function openssl-cert-check () {
    echo | \
    openssl s_client -servername $1 -connect ${3:-${1}}:${2:-443} 2>/dev/null | \
    openssl x509 -noout -text
}

function openssl-key-match () {
    echo | \
    echo "${1}.key"
    openssl rsa -noout -modulus -in ${1}.key  2> /dev/null | openssl md5
    echo "${1}.crt"
    openssl x509 -noout -modulus -in ${1}.crt 2> /dev/null | openssl md5
}

function dive () {
  if [ -z "$(docker images -q wagoodman/dive:latest 2> /dev/null)" ]; then
    docker pull wagoodman/dive:latest
  fi
  if [ -z "$(docker images -q ${1} 2> /dev/null)" ]; then
    docker pull ${1}
  fi

  docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest ${1}
}

function ghcr-login () {
    source ~/.env
    echo $GHCR_TOKEN | docker login ghcr.io -u jnovack --password-stdin
}

# Change Directory up to the root of the git repository
function cdroot() {
  current_dir=$(pwd)
  while [[ ! -d "$current_dir/.git" && "$current_dir" != "/" ]]; do
    current_dir=$(dirname "$current_dir")
  done
  if [[ -d "$current_dir/.git" ]]; then
    cd "$current_dir"
  else
    echo "No .git directory found in the directory tree."
  fi
}

function psync() {
  rsync -PLarvz -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "$@"
}

function exit() {
  # Check if inside a tmux session
  if [[ -n "$TMUX" ]]; then
    echo "Detaching from tmux session..."
    tmux detach
  else
    builtin exit "$@"
  fi
}

if [[ $- =~ i ]] && [[ -z "$TMUX" ]] && [[ -n "$SSH_TTY" ]] && command -v tmux >/dev/null 2>&1; then
  tmux attach-session -t ssh_tmux || tmux new-session -s ssh_tmux
fi

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion


export SDKROOT="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null)"

if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

if command -v brew >/dev/null 2>&1; then
  # Load azure completions
  [[ -s "$(brew --prefix)/etc/bash_completion.d/az" ]] && . "$(brew --prefix)/etc/bash_completion.d/az"
fi

if command -v go >/dev/null 2>&1; then
  export PATH="$(go env GOPATH)/bin:$PATH"
fi

# graperoot
export PATH="$PATH:$HOME/.dual-graph"

# Open VS Code: if a *.local.code-workspace file exists in the target directory,
# open that instead of the folder so folderOpen tasks (e.g. dual-graph MCP) fire.
function code() {
  local target="${1:-.}"
  if [[ $# -le 1 && -d "$target" ]]; then
    local ws
    ws=$(ls "$target"/*.local.code-workspace 2>/dev/null | head -1)
    if [[ -n "$ws" ]]; then
      command code "$ws" "${@:2}"
      return
    fi
  fi
  command code "$@"
}

export PATH="$HOME/.local/bin:$PATH"

_load_ca_bundle() {
    local cert_dir="${HOME}/.certs"
    local bundle="${cert_dir}/.bundle.pem"
    [[ -d "$cert_dir" ]] || return
    cat "$cert_dir"/*.pem(N) > "$bundle" 2>/dev/null
    [[ -s "$bundle" ]] && export CURL_CA_BUNDLE="$bundle" SSL_CERT_FILE="$bundle"
}
_load_ca_bundle

if [[ -f "$HOME/.zshrc.local" ]]; then
  source "$HOME/.zshrc.local"
fi
