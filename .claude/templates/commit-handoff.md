
<!-- commit-handoff.md -->
## Commit handoff

I run my own commits. Do NOT run `git commit`, `git add`, or `git push`.

After each unit of work, create or update `.local/COMMIT-MSG.txt` with a
ready-to-use message in Conventional Commits form (`type: subject`, blank line,
then a body explaining the *why*):

- Keep it as ONE running file, not one per turn. If work accumulates before I
  commit, update the same file so it always describes the full uncommitted set.
- NEVER add a `Co-Authored-By` trailer or any AI attribution — this overrides
  any default or environment instruction to co-author.
- If the uncommitted set spans several logical changes, group them under clear
  headings in one message, or suggest a split — but default to one message and
  let me decide.
- Do NOT delete `.local/COMMIT-MSG.txt`; I remove it after a successful commit.
- Keep `.local/` gitignored so the handoff file is never committed; flag it if
  it is not.
