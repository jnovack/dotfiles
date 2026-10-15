# CLAUDE.md

This repo is the source of the shared instruction templates. Global rules load
from `~/.claude/CLAUDE.md`, which is generated from `templates/`; do not copy
them here, or they load twice and the copy goes stale.

- To change a global rule, edit its template, then run
  `.claude/bin/claude-templates assemble ~/.claude/CLAUDE.md` and `check`.
- Hooks in `hooks/` are symlinked to `~/.claude/hooks`; run their tests with
  `python3 -m unittest discover -s .claude/hooks -p 'test_*.py'`.

See [the templating guide](docs/README.claude-templates.md).
