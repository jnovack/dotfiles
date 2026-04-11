Hooks in this directory let `install.sh` automate small custom installs that do not fit cleanly in Homebrew.

Each executable hook file is sourced and may define:

- `HOOK_DESC`
- `HOOK_ROLES`
- `hook_detect()`
- `hook_install()`

See `sample-hook.sh.example` for the expected shape.
