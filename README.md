# dotfiles

This repo now serves two jobs:

- bootstrap a new macOS workstation
- keep shared shell and git configuration synchronized with local escape hatches

The current system is built around three commands:

- `install.sh` for first-run setup
- `sync.sh` for canonical dotfile linking
- `audit.sh` for migration guidance on existing machines

## Bootstrap

Run this on a new Mac:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/jnovack/dotfiles/HEAD/install.sh)"
```

The installer will:

- ensure Xcode Command Line Tools and Homebrew are available
- clone or refresh the repo in `~/Source/dotfiles`
- prompt for a machine role
- install baseline apps and tools
- install `oh-my-zsh` and `powerlevel10k`
- install Meslo Nerd Font for `powerlevel10k` terminal glyphs
- sync canonical `.zshrc`, `.gitconfig`, and `.p10k.zsh`

## Sync Model

The repo owns the canonical shared files:

- `.zshrc`
- `.gitconfig`
- `.p10k.zsh`

They are symlinked into `$HOME` by `sync.sh`.

Machine-local additions live outside the repo:

- `~/.zshrc.local`
- `~/.gitconfig.local`
- `~/.p10k.local.zsh`

The canonical files load those local companions natively, so there is no generated merged file to maintain.

## Audit

Use `./audit.sh` on existing machines before syncing. It will review:

- package drift against the registry in `packages/`
- `.zshrc` drift versus the canonical repo file
- `.gitconfig` drift versus the canonical repo file
- presence of local companion files
- shell tooling like `oh-my-zsh`, `powerlevel10k`, and the current login shell

## Package Maintenance

The package registry is intentionally simple:

- shared formulas: `packages/formulas.txt`
- shared casks: `packages/casks.txt`
- role-based additions: `packages/roles/*.txt`
- custom installers: `hooks/*.sh`

Routine changes should mostly mean editing those files, not rewriting the installer.
