Run a multi-agent parallel code review of the repository and produce `.local/REVIEW.md`.

If a path argument is provided (e.g. `/review-comprehensive src/`), scope all file
discovery to that path. Otherwise review the full repository.

Before writing, ensure `.local/` exists. If `.local/.gitignore` does not exist,
create it with:

```text
*
!.gitignore
```

---

## Instructions

Invoke the **Workflow tool** with the script below. Pass any path argument as `args`.

This command fans out **6 parallel agents**, each reading all files in scope but
hunting only one analysis dimension. A synthesis agent deduplicates and writes
`.local/REVIEW.md`. Token cost is approximately 5× a standard `/review` run; use
this command when coverage matters more than speed.

---

## Workflow Script

```javascript
export const meta = {
  name: 'review-comprehensive',
  description: 'Multi-agent parallel code review across 6 dimensions',
  phases: [
    { title: 'Discover' },
    { title: 'Analyze' },
    { title: 'Synthesize' },
  ],
}

phase('Discover')
const scope = args || '.'
const discovery = await agent(
  'List every source file under the path "' + scope + '". ' +
  'Exclude: build artifacts, vendored or third-party dependencies, ' +
  'generated files (*.pb.go, *.gen.*, dist/, vendor/), lockfiles, ' +
  'and binary files. ' +
  'Also write one sentence describing the languages and top-level ' +
  'structure found. Return JSON.',
  {
    label: 'discover',
    schema: {
      type: 'object',
      properties: {
        files: { type: 'array', items: { type: 'string' } },
        summary: { type: 'string' }
      },
      required: ['files', 'summary']
    }
  }
)

if (!discovery || discovery.files.length === 0) {
  log('No source files found in scope: ' + scope)
  return { findings: [] }
}

const FILE_LIST = discovery.files.join('\n')
const SUMMARY = discovery.summary

const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file:         { type: 'string' },
          lines:        { type: 'string' },
          severity:     { type: 'string', enum: ['critical','high','medium','low'] },
          title:        { type: 'string' },
          issue:        { type: 'string' },
          fix:          { type: 'string' },
          fix_language: { type: 'string' },
          rationale:    { type: 'string' },
          test:         { type: 'string' }
        },
        required: ['file','lines','severity','title','issue','fix','rationale']
      }
    }
  },
  required: ['findings']
}

const BASE =
  'Only report findings supported by concrete code evidence representing a real ' +
  'bug, security risk, reliability issue, or meaningful maintainability problem. ' +
  'Do not speculate. Do not flag risks already handled elsewhere in the codebase. ' +
  'Verify exact line numbers before reporting.\n\n' +
  'Repository: ' + SUMMARY + '\n\n' +
  'Files to read:\n' + FILE_LIST

const DIMENSIONS = [
  {
    key: 'null-errors',
    prompt: 'You are reviewing for ABSENT-VALUE SAFETY and ERROR PROPAGATION only.\n' +
      BASE + '\n\n' +
      'Check:\n' +
      '1. Every value that could be null, nil, None, undefined, empty, ' +
        'zero-value-invalid, or a typed null — is it checked before use?\n' +
      '2. Every operation that can fail — is the error/exception checked? ' +
        'Does propagation preserve cause/context? Is nothing silently ' +
        'swallowed or replaced with a misleading message?\n\n' +
      'Ignore all other issue types.'
  },
  {
    key: 'resources',
    prompt: 'You are reviewing for RESOURCE LIFECYCLE only.\n' +
      BASE + '\n\n' +
      'Check: every file handle, connection, lock, socket, goroutine, thread, ' +
      'timer, ticker, request body, response body, or allocated resource — is ' +
      'there a guaranteed release on all exit paths including error paths?\n\n' +
      'Ignore all other issue types.'
  },
  {
    key: 'concurrency',
    prompt: 'You are reviewing for CONCURRENCY only.\n' +
      BASE + '\n\n' +
      'Check: every value accessed from multiple goroutines/threads/tasks — is ' +
      'it synchronized or immutable? Every async operation — is its lifetime ' +
      'bounded, cancellable where appropriate, and failure observable?\n\n' +
      'Ignore all other issue types.'
  },
  {
    key: 'security',
    prompt: 'You are reviewing for SECURITY only.\n' +
      BASE + '\n\n' +
      'Check all three areas:\n' +
      '1. Trust boundary validation — every value from user input, env vars, ' +
        'config, external APIs, CLI args, HTTP headers, serialized data, or ' +
        'filesystem state — validated or sanitized before use?\n' +
      '2. Credential/secret exposure — can any variable, field, error message, ' +
        'panic, response, metric, trace, or log line leak a secret, key, token, ' +
        'credential, or PII?\n' +
      '3. Injection surfaces — every place external data is composed into a ' +
        'query, shell command, template, URL, HTTP header, regex, file path, ' +
        'archive path, or code expression — escaped, parameterized, ' +
        'allowlisted, or otherwise safe?\n\n' +
      'Ignore all other issue types.'
  },
  {
    key: 'tests',
    prompt: 'You are reviewing for BASIC TEST COMPLETENESS only.\n' +
      BASE + '\n\n' +
      'Check: for each tested function or behavior — are negative cases present? ' +
      'Boundary conditions? Error paths? Do tests rely on timing assumptions, ' +
      'global state mutation, ordering, network access, local machine state, or ' +
      'implementation details? Also flag any exported or public function with ' +
      'zero test coverage.\n\n' +
      'Note: you are NOT performing a comprehensive test audit — that is ' +
      '/review-tests. Only flag clear, obvious deficiencies.\n\n' +
      'Ignore all other issue types.'
  },
  {
    key: 'consistency',
    prompt: 'You are reviewing for CONVENTION CONSISTENCY only.\n' +
      BASE + '\n\n' +
      'Identify the naming, error-handling, logging, testing, and structural ' +
      'patterns already established in this codebase, then flag deviations. ' +
      'Do not flag stylistic preferences — only deviations from patterns the ' +
      'codebase has already committed to.\n\n' +
      'Ignore all other issue types.'
  }
]

phase('Analyze')

const results = await parallel(
  DIMENSIONS.map(d => () =>
    agent(d.prompt, {
      label: 'analyze:' + d.key,
      phase: 'Analyze',
      schema: FINDING_SCHEMA
    })
  )
)

phase('Synthesize')

const allFindings = results.filter(Boolean).flatMap(r => r.findings)
log(allFindings.length + ' raw findings from ' + DIMENSIONS.length +
  ' dimensions — deduplicating and writing report')

await agent(
  'You have ' + allFindings.length + ' raw findings from ' + DIMENSIONS.length +
  ' parallel code reviewers.\n\n' +
  'Repository: ' + SUMMARY + '\n\n' +
  'Instructions:\n' +
  '1. Deduplicate: same file+lines reported by multiple agents — keep the most ' +
     'specific description.\n' +
  '2. Assign severity consistently: Critical (crash/data-loss/exploitable), ' +
     'High (likely bug or significant security weakness), Medium (will cause ' +
     'problems at scale), Low (minor refinement).\n' +
  '3. Assign IDs: #MODULE-TYPE-NN where MODULE is a 2-4 char file abbreviation, ' +
     'TYPE is a 2-4 char issue class (NULL INJ RACE LEAK SEC ERR etc.), ' +
     'NN is a 2-digit 1-based counter reset per module-type pair.\n' +
  '4. Write the complete .local/REVIEW.md file.\n\n' +
  'REVIEW.md format:\n' +
  '- # Code Review header with generated datetime, reviewer, scope\n' +
  '- ## Summary (3-5 sentences: dominant patterns, highest-priority concerns)\n' +
  '- ## Finding Index (table: ID | Severity emoji+label | File | Title)\n' +
  '- ## Findings by File (per-file blocks ordered by highest severity in that ' +
     'file; each finding block: severity emoji heading with ID, Line(s), Issue, ' +
     'Fix as a complete runnable fenced code block with language tag, ' +
     'Rationale, Test)\n' +
  '- ## Severity Reference (4-level table with emoji labels)\n' +
  '- ## Quick Wins (3-5 highest-leverage changes)\n' +
  '- If no findings: say so and note where static analysis has limited coverage.\n\n' +
  'Severity emoji prefix: Critical = red circle, High = orange circle, ' +
  'Medium = yellow circle, Low = blue circle.\n\n' +
  'Findings JSON:\n' + JSON.stringify(allFindings, null, 2),
  { label: 'synthesize' }
)
```
