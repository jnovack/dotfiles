# /adr — Record an Architecture Decision

Run this only after a plan has been fully executed, not during planning.

1. Review what was just built or changed in this session
2. Determine if any decisions meet the ADR trigger criteria in CLAUDE.md
   - If none qualify, say so explicitly and stop
3. Check /docs/decisions/ for the next sequence number
4. For each qualifying decision, write `docs/decisions/NNNN-<kebab-title>.md`:

---
# NNNN. <Title>

**Date:** <today>

**Status:** Accepted

Describe the context and problem statement using two to three sentences along
with the decision.

## Context

What situation or constraint forced this decision?
What would have happened without it?

## Alternatives Considered

The numbers of options may vary, utilize this format.

**Option Summary** - Why this option was rejected

**Option Summary** - Why this option was rejected

## Consequences

**Easier:** what this decision enables

**Harder:** what this decision complicates or forecloses

**Constrains:** future decisions this limits

## More Information

Provide additional evidence/confidence for the decision outcome here and define
the when/how of this decision.  Document when the decision should be realized,
if/when it should be re-visited, and links to other decisions and resources.

---

1. Update /docs/decisions/README.md index
2. Add a reference comment to any module created or significantly affected:
   `adr#NNNN-<kebab-title>.md` at the top of the file or function.

Do not editorialize. Do not retroactively justify. Record what actually happened.
