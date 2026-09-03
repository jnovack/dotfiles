# git release

`git release` tags a version and pushes it. When the repo opts in, it also
writes that version into whatever files the repo keeps it in — so the tag and
the manifest can never disagree.

The alias itself knows nothing about npm, Go modules, or Cargo. It does tag math
and delegates the rest to a script inside the repo.

## Usage

```sh
git autocommit                 # working tree must be clean before releasing
git release minor              # v0.3.0 -> v0.4.0
git release patch "hotfix"     # optional annotation message
git release v1.0.0             # explicit, for anything the math won't produce
```

`major` / `minor` / `patch` count up from the newest tag matching
`v[0-9]*.[0-9]*.[0-9]*`. There is no other input: the newest tag is the current
version, by definition.

## What it does, in order

1. Resolve the version (`$ver`) from tag math or the explicit argument.
2. **If `$(git rev-parse --show-toplevel)/.githooks/version` is executable:**
   - refuse to continue if the working tree is dirty, so unrelated work cannot
     land in the release commit;
   - run `.githooks/version write <x.y.z>` (no leading `v`);
   - if that changed tracked files, commit them as `chore(release): vX.Y.Z` and
     push.
3. Create the annotated tag.
4. For a **non-prerelease** version, force-move the floating `vX` and `vX.Y`
   tags to it and push those too. A version containing `-` (`v1.0.0-rc.1`) is
   treated as a prerelease and moves no floating tags.
5. Push the version tag.

A repo without `.githooks/version` skips step 2 entirely and behaves exactly as
it always has. Go repos that read their version from the tag — via `ldflags` or
`debug.ReadBuildInfo` — need no file and no change.

## The repo-side contract

Two subcommands, both driven from the repo root:

| Command | Must do |
| --- | --- |
| `.githooks/version read [<rev>]` | Print the version recorded in the repo, from the worktree or from `<rev>`. Used by the push guard. |
| `.githooks/version write <x.y.z>` | Write that version everywhere the repo records it, and regenerate anything derived from it. Non-zero exit aborts the release before any tag exists. |

`write` is the right place for tests and builds: a version that fails its own
test suite should never reach a tag, and generated artifacts that embed the
version are part of applying it, not a chore to remember afterwards.

### Node opt-in

```sh
#!/bin/sh
set -e
cd "$(git rev-parse --show-toplevel)"
case "$1" in
    read)  if [ -n "$2" ]; then git show "$2:package.json"; else cat package.json; fi | jq -er .version ;;
    write) npm version "$2" --no-git-tag-version --allow-same-version >/dev/null
           npm test >/dev/null
           npm run build >/dev/null ;;
esac
```

`npm version --no-git-tag-version` updates `package.json` **and** both
`package-lock.json` version entries, so no hand-rolled JSON writer is needed.

`scryfall-query-dsl` is the worked example: it also promotes its
`## [Unreleased]` changelog section to the released version and regenerates its
docs site. See `.githooks/version` and `scripts/changelog-release.mjs` there.

### Go opt-in

Usually none. If the repo embeds a constant rather than reading the tag:

```sh
#!/bin/sh
set -e
cd "$(git rev-parse --show-toplevel)"
case "$1" in
    read)  if [ -n "$2" ]; then git show "$2:internal/version/version.go"; else cat internal/version/version.go; fi \
             | sed -nE 's/.*Version = "([^"]+)".*/\1/p' ;;
    write) sed -i '' -E "s/(Version = )\"[^\"]+\"/\1\"$2\"/" internal/version/version.go
           go test ./... >/dev/null ;;
esac
```

## The push guard

`.githooks/pre-push` rejects a pushed tag `vX.Y.Z` whose version disagrees with
`.githooks/version read <that commit>`. It exists for the path that bypasses the
alias — a hand-typed `git tag`.

Git has **no pre-tag hook**, so push is the earliest possible enforcement point.
A rejected tag still exists locally:

```sh
git tag -d v1.2.3        # then release properly
```

The guard must ignore branch pushes, tag deletions, and the floating `vX` /
`vX.Y` refs — those are not full versions and rejecting them would fail every
non-prerelease release.

## Installing the hooks

Hooks live in the repo (`.githooks/`) so they are shared and reviewable, which
means each clone must be pointed at them:

```sh
git config core.hooksPath .githooks
```

Automate it per ecosystem — a `prepare` script in `package.json` for Node, a
`make setup` target for Go. Until someone runs it, a fresh clone is unguarded.

## Gotchas

- Tag math counts from the newest tag *including prereleases*, so `patch` after
  `v1.0.0-rc.3` gives `v1.0.1`, not `v1.0.0`. Land a final release after RCs
  with the explicit form: `git release v1.0.0`.
- A build that embeds the commit sha alongside the version names the release
  commit's *parent*, since the sha is read before the commit exists.
- The alias uses `--show-toplevel`, so it works from a subdirectory. A relative
  path would silently skip the delegation and let drift back in.
