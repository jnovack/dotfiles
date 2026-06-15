# /todo-checkpoint

Validate that a completed TODO item satisfies its Definition of Done.

## What to do

### 1 — Identify the item

If an ID argument was provided, use it.

Otherwise, scan `TODO.md` for the most recently completed item — the last row with status `done`.

- If no item is identified: report "No completed items found. Provide an ID or complete an item first." and stop.

Read `.claude/todos/<id>.plan.md` to get the DoD checklist (core and any optional items declared).

- If the plan file is missing: report it and proceed with core DoD only — flag the missing plan as a WARN.

### 2 — Detect and run tests

Detect the project test command in this order:

1. `go.mod` present → `go test ./...`
2. `Makefile` present with a `test` target → `make test`
3. `package.json` present with a `"test"` script → `npm test`
4. `pytest.ini`, `pyproject.toml`, or `setup.py` present → `pytest`

If none detected: report "Could not detect test command — run tests manually and confirm pass." Treat as WARN for this criterion only, not FAIL.

If a command is detected and tests **fail**:

- Report which tests failed.
- Mark the checkpoint **FAILED — tests**.
- Stop. Do not proceed to remaining checks.

### 3 — Check DoD criteria

Report PASS, FAIL, or WARN for each:

**Tests** — result from step 2.

**Docs** — check whether any of the following were relevant to the change and, if so, whether they were updated:

- `README.md` (flags, env vars, runtime behavior)
- API docs / `docs/openapi.yaml`
- `AGENTS.md` (architecture contracts)
- `doc.go` in any affected package

FAIL if a relevant doc was not updated.

**Technical debt** — are any new `// TODO` or `// FIXME` markers introduced by this work? If so, do they each have a corresponding entry in `TODO.md`? Untracked debt = FAIL.

**Optional items** — for each optional item declared in the plan's DoD checklist, check whether it was completed. FAIL if a declared optional item was not completed.

### 4 — Report

```text
═══════════════════════════════════════
 Checkpoint — <id> — <summary>
═══════════════════════════════════════
 Tests            PASS / FAIL / WARN — [note]
 Docs             PASS / FAIL / WARN — [note]
 Technical debt   PASS / FAIL — [note]
 <one line per optional item, if any>
───────────────────────────────────────
 Overall:  PASS — item is complete
        or FAIL — [N] criteria not met
        or WARN — can advance, review [items]
═══════════════════════════════════════
```

**On FAIL:** List exactly what needs to be fixed. Do not advance the item.

**On WARN:** The item can stand. Call out what to revisit.

**On PASS:** Confirm the item's status in `TODO.md` is `done` (update it if not). Tell the user to run `/todo-next` for the next item.
