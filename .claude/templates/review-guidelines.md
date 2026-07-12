---
id: review-guidelines
scope: project
order: 44
---

## Review guidelines

When reviewing planning or task documents such as PLAN.md and TODO.md:

- Verify all claims against the repository, not assumptions.
- Flag missing rollout, rollback, migration, testing, and observability steps.
- Flag tasks that are not actionable or cannot be validated.
- Check that TODO items map cleanly to the plan.
- Call out security risks including secrets handling, auth/authz gaps, unsafe
  defaults, excessive permissions, insecure transport, logging of sensitive
  data, and shell injection risk.
- Prefer minimal, concrete findings over broad rewrites.
- Do not edit files unless explicitly asked.
