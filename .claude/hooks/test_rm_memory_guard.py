"""Tests for rm-memory-guard.py, run through its real stdin/stdout contract.

Run: python3 -m unittest discover -s .claude/hooks -p 'test_*.py'

Every test points HOME at a temp dir holding fake memory files, so the real
~/.claude/projects is never read.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rm-memory-guard.py")


def encode(path):
    # Own copy of the hook's encoding, on purpose: a test that imported the
    # hook's encoder could not catch a wrong encoder.
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def run(payload, home):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=raw,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "HOME": home},
    )
    return proc.returncode, proc.stdout.strip()


def rm(command, cwd):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    if cwd is not None:
        payload["cwd"] = cwd
    return payload


class RmMemoryGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.home = os.path.join(self.root, "home")
        os.makedirs(self.home)
        self.repoa = self.make_repo("src/repoa")
        self.repob = self.make_repo("src/repob")

    def make_repo(self, rel):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.join(path, ".git"))
        return path

    def memory(self, project_path, text, use_realpath=False, home=None):
        path = os.path.realpath(project_path) if use_realpath else project_path
        folder = os.path.join(home or self.home, ".claude", "projects", encode(path), "memory")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "note.md"), "w", encoding="utf-8") as handle:
            handle.write(text + "\n")

    def out(self, payload, home=None):
        code, out = run(payload, home or self.home)
        self.assertEqual(code, 0)
        return out

    def denied(self, payload, home=None):
        out = self.out(payload, home)
        if not out:
            return False
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_other_repos_review_md_memory_does_not_block(self):
        # The 2026-11-10 incident: meal-ticket's memory denied dotfiles' delete.
        self.memory(self.repob, "see review finding in this repo's `.local/REVIEW.md` history")
        # Allowed via the exemption alone (memory is never scanned for it).
        self.assertFalse(self.denied(rm("rm .local/REVIEW.md", self.repoa)))
        # Non-exempt name proves the repo scoping on its own. (memory() rewrites
        # repob's note.md.)
        self.memory(self.repob, "commit handoff in `.local/COMMIT-MSG.txt`")
        self.assertFalse(self.denied(rm("rm .local/COMMIT-MSG.txt", self.repoa)))

    def test_review_reports_exempt_even_in_own_repo(self):
        self.memory(
            self.repoa,
            "`.local/REVIEW.md`\n`.local/REVIEW.DEPS.md`\n`.local/ASSESSMENT.md`",
        )
        for name in ("REVIEW.md", "REVIEW.DEPS.md", "ASSESSMENT.md"):
            with self.subTest(name=name):
                self.assertFalse(self.denied(rm("rm .local/" + name, self.repoa)))

    def test_review_md_outside_local_not_exempt(self):
        self.memory(self.repoa, "keep `docs/REVIEW.md`")
        os.makedirs(os.path.join(self.repoa, "docs"))
        self.assertTrue(self.denied(rm("rm docs/REVIEW.md", self.repoa)))

    def test_own_repo_plan_md_still_denied(self):
        # The original incident: .local/PLAN.md was the only copy.
        self.memory(self.repoa, "`.local/PLAN.md` is the ONLY copy")
        command = "rm .local/PLAN.md"
        out = self.out(rm(command, self.repoa))
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("`.local/PLAN.md` is the ONLY copy", decision["permissionDecisionReason"])
        self.assertIn(command, decision["permissionDecisionReason"])

    def test_cross_repo_line_naming_repo_dir_denies(self):
        self.memory(self.repob, "global todos live in src/repoa/.local/TODO.md")
        self.assertTrue(self.denied(rm("rm .local/TODO.md", self.repoa)))
        # memory() rewrites repob's note.md, so the repo-naming line is gone here.
        self.memory(self.repob, "global todos live in .local/TODO.md")
        self.assertFalse(self.denied(rm("rm .local/TODO.md", self.repoa)))

    def test_encoded_prefix_project_is_not_ancestor(self):
        meal_ticket = self.make_repo("src/meal-ticket")
        # Project path `src/meal` encodes to a string prefix of `src/meal-ticket`.
        self.memory(os.path.join(self.root, "src", "meal"), "`.local/PLAN.md` matters")
        self.assertFalse(self.denied(rm("rm .local/PLAN.md", meal_ticket)))

    def test_no_git_ancestor_falls_back_to_global(self):
        loose = os.path.join(self.root, "loose")
        os.makedirs(loose)
        self.memory(self.repob, "remember notes.md")
        self.assertTrue(self.denied(rm("rm notes.md", loose)))

    def test_cd_segment_falls_back_to_global(self):
        self.memory(self.repob, "todos in .local/TODO.md")
        self.assertTrue(self.denied(rm("cd %s && rm .local/TODO.md" % self.repob, self.repoa)))
        self.assertTrue(self.denied(rm("(cd %s && rm .local/TODO.md)" % self.repob, self.repoa)))

    def test_same_basename_in_two_repos_keeps_both_scopes(self):
        # Memory belongs to the FIRST target's repo: a last-wins scope store
        # would keep only repoa's scope and wrongly allow.
        self.memory(self.repob, "todos in .local/TODO.md")
        command = "rm %s/.local/TODO.md %s/.local/TODO.md" % (self.repob, self.repoa)
        self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_absolute_target_scoped_to_its_repo(self):
        self.memory(self.repob, "handoff `.local/COMMIT-MSG.txt`")
        command = "rm %s/.local/COMMIT-MSG.txt" % self.repoa
        self.assertFalse(self.denied(rm(command, None)))
        self.memory(self.repoa, "handoff `.local/COMMIT-MSG.txt`")
        self.assertTrue(self.denied(rm(command, None)))

    def test_abspath_and_realpath_project_forms_match(self):
        for use_realpath in (False, True):
            with self.subTest(use_realpath=use_realpath):
                home = os.path.join(self.root, "home-%s" % use_realpath)
                os.makedirs(home)
                self.memory(self.repoa, "`.local/PLAN.md` only copy", use_realpath, home)
                self.assertTrue(self.denied(rm("rm .local/PLAN.md", self.repoa), home))

    def test_shell_expanded_target_falls_back_to_global(self):
        # Review R-01: `$REPOB/...` joined to cwd scoped the delete to repo A.
        self.memory(self.repob, "`.local/PLAN.md` is the ONLY copy")
        for command in ("rm $REPOB/.local/PLAN.md", "rm $(pwd)/.local/PLAN.md", "rm `pwd`/.local/PLAN.md"):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_cd_behind_group_or_keyword_falls_back_to_global(self):
        # Review R-02: `{ cd B`, `then cd B` and `do cd B` hid the cd.
        self.memory(self.repob, "todos in .local/TODO.md")
        for template in (
            "{ cd %s; rm .local/TODO.md; }",
            "if true; then cd %s; rm .local/TODO.md; fi",
            "for x in y; do cd %s && rm .local/TODO.md; done",
        ):
            command = template % self.repob
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_grouped_rm_is_recognised(self):
        self.memory(self.repoa, "`.local/PLAN.md` is the ONLY copy")
        for command in ("(rm .local/PLAN.md)", "{ rm .local/PLAN.md; }", "rm -- .local/PLAN.md"):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_subdirectory_session_memory_guards_repo_file(self):
        # Review R-03: memory from a session started in repoa/cmd is repo A's own.
        self.memory(os.path.join(self.repoa, "cmd"), "`.local/PLAN.md` is the ONLY copy")
        self.assertTrue(self.denied(rm("rm .local/PLAN.md", self.repoa)))

    def test_exempt_report_does_not_shield_guarded_sibling(self):
        self.memory(self.repoa, "`.local/REVIEW.md` and `.local/PLAN.md` only copy")
        self.assertTrue(self.denied(rm("rm .local/REVIEW.md .local/PLAN.md", self.repoa)))

    def test_existing_non_matches_stay_silent(self):
        self.memory(self.repoa, "`.local/PLAN.md` and ab and rm")
        for payload in (
            rm("ls -la", self.repoa),
            rm("echo rm .local/PLAN.md", self.repoa),
            rm("rm -rf", self.repoa),
            rm("rm ab", self.repoa),
            "not json",
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.out(payload), "")

    # --- FIX-MEMGUARD-02: quote-aware segment split -------------------------

    PLAN_MEMORY = "`.local/PLAN.md` is the ONLY copy"

    def touch(self, repo, rel):
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8"):
            pass

    def test_separator_inside_quotes_is_not_a_split(self):
        # A quoted `|`/`;`/newline started a fake segment whose unbalanced quote
        # fell back to whitespace splitting and read `rm` as a leader.
        self.memory(self.repoa, self.PLAN_MEMORY)
        for command in (
            "grep -E 'foo\\|rm .local/PLAN.md now' notes.txt",
            'echo "done; rm .local/PLAN.md later" && ls',
            "printf 'a\nrm .local/PLAN.md b'",
            "git commit -m 'a && rm .local/PLAN.md b'",
            "grep -E 'foo|rm .local/PLAN.md'",
        ):
            with self.subTest(command=command):
                self.assertFalse(self.denied(rm(command, self.repoa)))

    def test_quoted_or_escaped_punctuation_token_is_data(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        for command in ("echo ';' rm .local/PLAN.md", "echo \\; rm .local/PLAN.md"):
            with self.subTest(command=command):
                self.assertFalse(self.denied(rm(command, self.repoa)))

    def test_rm_segment_only_not_following_echo_prose(self):
        # Recorded in the docstring; had no test.
        self.memory(self.repoa, "files added during migration")
        self.assertFalse(self.denied(rm('rm -f x && echo "=== files added ==="', self.repoa)))

    def test_redirects_background_and_group_still_deny(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        for command in (
            "rm .local/PLAN.md 2>&1",
            "rm .local/PLAN.md >&2",
            "rm .local/PLAN.md &>log",
            "rm .local/PLAN.md &>>log",
            "rm .local/PLAN.md &",
            "(rm .local/PLAN.md)",
            "true && rm .local/PLAN.md",
            "false || rm .local/PLAN.md",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_comment_ends_at_newline_not_at_end_of_command(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        self.assertTrue(self.denied(rm("echo ok # comment\nrm .local/PLAN.md", self.repoa)))
        # Quoted `#` is data, and a comment hides what follows on its own line.
        self.assertFalse(self.denied(rm("echo ok # rm .local/PLAN.md", self.repoa)))

    def test_escaped_newline_is_a_continuation_not_a_command_boundary(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        self.assertFalse(self.denied(rm("echo ok\\\nrm .local/PLAN.md", self.repoa)))

    def test_double_quote_escape_semantics(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        allow = (
            'echo "a\\" ; rm .local/PLAN.md b"',  # escaped quote keeps the string open
            'echo "a\\; rm .local/PLAN.md"',  # backslash before ordinary char inside quotes
        )
        deny = (
            "echo 'a\\'; rm .local/PLAN.md",
            'echo "a\\q" ; rm .local/PLAN.md',
            'echo "a\\"" ; rm .local/PLAN.md',
        )
        for command in allow:
            with self.subTest(command=command):
                self.assertFalse(self.denied(rm(command, self.repoa)))
        for command in deny:
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_unbalanced_quotes_keep_fallback(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        # Malformed rm: guarding is preferred over silently allowing.
        self.assertTrue(self.denied(rm("rm .local/PLAN.md 'oops", self.repoa)))
        # Malformed non-rm text: no crash, no output.
        self.assertEqual(self.out(rm("echo 'oops && ls", self.repoa)), "")
        self.assertEqual(self.out(rm('echo "oops rm', self.repoa)), "")

    # --- FIX-MEMGUARD-02: glob targets --------------------------------------

    def test_glob_expands_against_cwd_and_denies(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        self.touch(self.repoa, ".local/PLAN.md")
        for command in ("rm .local/PLAN*.md", "rm .local/PLA?.md", "rm .local/PLAN.[m]d"):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_glob_match_keeps_repo_scoping(self):
        self.memory(self.repob, self.PLAN_MEMORY)
        self.touch(self.repoa, ".local/PLAN.md")
        self.assertFalse(self.denied(rm("rm .local/PLAN*.md", self.repoa)))

    def test_glob_after_cd_falls_back_to_global_pattern(self):
        self.memory(self.repob, self.PLAN_MEMORY)
        command = "cd %s && rm .local/PLAN*.md" % self.repob
        self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_glob_with_expanded_directory_falls_back_to_global_pattern(self):
        self.memory(self.repob, self.PLAN_MEMORY)
        for command in (
            "rm $REPOB/.local/PLAN*.md",
            "rm $(pwd)/.local/PLAN*.md",
            "rm `pwd`/.local/PLAN*.md",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_glob_without_filesystem_match_uses_memory_pattern(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        self.assertTrue(self.denied(rm("rm .local/PLAN*.md", self.repoa)))

    def test_glob_without_memory_match_allows(self):
        self.memory(self.repoa, self.PLAN_MEMORY)
        self.touch(self.repoa, ".local/a.tmp")
        self.assertFalse(self.denied(rm("rm .local/*.tmp", self.repoa)))
        self.assertFalse(self.denied(rm("rm .local/nothing*.tmp", self.repoa)))

    def test_glob_exempt_report_alone_allows_but_guarded_sibling_denies(self):
        self.memory(self.repoa, "`.local/REVIEW.md` and `.local/PLAN.md` only copy")
        self.touch(self.repoa, ".local/REVIEW.md")
        self.assertFalse(self.denied(rm("rm .local/REVIEW*.md", self.repoa)))
        self.touch(self.repoa, ".local/PLAN.md")
        self.assertTrue(self.denied(rm("rm .local/*.md", self.repoa)))
        # An exempt glob must not hide a guarded literal sibling.
        self.assertTrue(self.denied(rm("rm .local/REVIEW*.md .local/PLAN.md", self.repoa)))

    def test_glob_min_token_length_applies(self):
        self.memory(self.repoa, "keep a1 and abcd.txt and `.local/PLAN.md`")
        # Fallback pattern `a*` is shorter than MIN_TOKEN_LEN: ignored.
        self.assertFalse(self.denied(rm("rm a*", self.repoa)))
        # Expansion: the short basename is ignored, PLAN.md is guarded.
        self.touch(self.repoa, "x/a1")
        self.assertFalse(self.denied(rm("rm x/*", self.repoa)))
        self.touch(self.repoa, "x/PLAN.md")
        self.assertTrue(self.denied(rm("rm x/*", self.repoa)))

    def test_glob_fallback_extracts_words_from_mixed_prose(self):
        self.memory(
            self.repob,
            "see (`docs/PLAN.md`), 'notes/OTHER.md'; and \"x.local/PLAN.md.\" ok",
        )
        for command in ("cd /tmp && rm PLAN*.md", "cd /tmp && rm OTH??.md"):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))
        self.assertFalse(self.denied(rm("cd /tmp && rm NOPE*.md", self.repoa)))

    def test_multiple_glob_patterns_each_checked(self):
        self.memory(self.repob, "only copy `.local/PLAN.md`")
        self.assertTrue(self.denied(rm("cd /tmp && rm zzzz*.md PLAN*.md", self.repoa)))

    def test_quoted_literal_name_with_glob_chars_still_matches(self):
        self.memory(self.repoa, "keep `.local/odd[1]name.md` safe")
        self.touch(self.repoa, ".local/odd[1]name.md")
        self.assertTrue(self.denied(rm("rm '.local/odd[1]name.md'", self.repoa)))

    def test_unmatched_exempt_report_glob_stays_exempt(self):
        # The loops run `rm -f .local/REVIEW*.md` whether or not a report exists;
        # an unmatched glob's memory fallback must not deny on `REVIEW.md` there.
        self.memory(self.repoa, "`.local/REVIEW.md` list and `.local/PLAN.md` only copy")
        for command in ("rm -f .local/REVIEW*.md", "cd /tmp && rm -f .local/REVIEW*.md"):
            with self.subTest(command=command):
                self.assertFalse(self.denied(rm(command, self.repoa)))
        # The exemption covers only report names under `.local/`.
        for command in ("rm .local/*.md", "rm docs/REVIEW*.md"):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))
        self.memory(self.repoa, "keep `.local/REVIEW_NOTES.md`")
        self.assertTrue(self.denied(rm("rm .local/REVIEW*.md", self.repoa)))

    def test_escaped_char_before_hash_or_ampersand_is_word_data(self):
        # `a\ #x` is one word (no comment) and `a\>&` is `a>` then `&`: the later
        # rm is a real command in both. Testing only the last buffered character
        # read the escaped space/`>` as bare and swallowed the rm.
        self.memory(self.repoa, self.PLAN_MEMORY)
        for command in ("echo a\\ #x; rm .local/PLAN.md", "echo a\\>& rm .local/PLAN.md"):
            with self.subTest(command=command):
                self.assertTrue(self.denied(rm(command, self.repoa)))

    def test_redirect_word_is_not_a_delete_target(self):
        # `2>/dev/null` as a target would make `null` a repo-scoped candidate.
        self.memory(self.repoa, "noise goes to /dev/null and `build.log`")
        for command in (
            "rm -f .local/scratch.md 2>/dev/null",
            "rm -f .local/scratch.md &>/tmp/build.log",
        ):
            with self.subTest(command=command):
                self.assertFalse(self.denied(rm(command, self.repoa)))


if __name__ == "__main__":
    unittest.main()
