---
id: code-review-graph
scope: global
order: 34
---

## MCP Tools: code-review-graph

When the session reports a code-review-graph, prefer its MCP tools over
Grep/Glob/Read for structural questions (callers, impact radius, tests for,
review context). Fall back to text search for what the graph does not cover,
such as markdown, fixtures and logs.
