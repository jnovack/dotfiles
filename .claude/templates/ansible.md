---
id: ansible
scope: project
order: 54
---

## Ansible

### Task rules

- Prefer idempotent tasks. Prefer built-in Ansible modules over `shell` or `command`.
- Use fully-qualified collection names (`ansible.builtin.copy`, not `copy`) —
  ansible-lint enforces this and short names are ambiguous across collections.
- When `command` or `shell` is required, set `changed_when` and `failed_when` appropriately.
- Use handlers for service reload/restart — do not restart services inline in tasks.
- Prefer explicit `name:` on every task.
- Avoid hardcoded environment-specific values in roles.

### Variable rules

- Put defaultable values in `defaults/main.yml`. Keep host/group-specific values in inventory.
- Respect existing variable precedence and naming conventions.
- Treat inventory and variable changes as high-impact — call out anything that affects multiple environments.

### Role rules

- Keep `tasks/`, `handlers/`, `templates/`, `files/`, `defaults/`, and `vars/` responsibilities clear.
- Do not move logic between roles unless required. Extend current patterns before introducing abstractions.
- Keep role boundaries intact.

### YAML style

- Preserve existing indentation and key ordering.
- Do not introduce YAML anchors, aliases, or complex merges unless already used in the repo.

### Validation

```bash
ansible-lint
ansible-playbook --syntax-check site.yml   # substitute the repo's entry playbook
ansible-playbook --check --diff site.yml   # dry run with diff
```

Always run `--syntax-check` before claiming a playbook change is correct.
Do not claim a playbook executed successfully unless it was actually run.

### Read order

When starting work in this repo:

1. Read `AGENTS.md` (or `CLAUDE.md`) first.
2. Load only the role, playbook, inventory, or variable files relevant to the task.
