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


if __name__ == "__main__":
    unittest.main()
