---
id: container
scope: project
requires: [shell]
order: 55
---

## Container conventions

- Treat the container as ephemeral; keep no persistent state beyond mounted
  volumes or what is injected at startup.
- Prefer environment variables for all configuration. Do not bake secrets or
  host-specific values into the image.
- When adding an environment variable, give it a sensible default and document
  it in `README.md`.
- Use the process supervisor / init system already in the image; do not
  introduce systemd or a second init system.
- Use the repo's existing log prefixes consistently.
- If adding an OS package, keep it minimal and prefer tools already in the base
  image; call out why and note any security considerations.
- Validate with the repo's container test workflow (e.g. `make docker-test` or
  the compose SUT under `test/`).
