"""Tests for plan-loop-check, run as a real process.

Run: python3 -m unittest discover -s .claude/bin -p 'test_*.py'
"""
import json
import os
import subprocess
import tempfile
import unittest

BIN = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(BIN, "plan-loop-check")

SETTINGS = {
    "permissions": {
        "allow": ["Bash(rsync *)"],  # allow never overrides deny
        "deny": [
            "Bash(rsync *)",
            "Bash(git commit *)",
            "Bash(nc *)",
            "Bash(* ~/.ssh/*)",
            "Bash(npm publish:*)",
            "Read(**/.env)",
        ],
        "ask": ["Bash(* /usr/bin/*)"],
    }
}


def plan(commands, unattended="yes", extra=""):
    front = "---\nid: FIX-THING-01\nmodel: sonnet\n"
    if unattended is not None:
        front += "unattended: %s\n" % unattended
    body = front + "---\n\n## Steps\n\n1. Do it.\n" + extra
    if commands is not None:
        body += "\n## Commands\n\n```bash\n" + commands + "\n```\n"
    return body + "\n## DoD Checklist\n\n- [ ] Tests pass\n"


class PlanLoopCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        os.makedirs(self.home)
        self.settings = os.path.join(self.tmp.name, "settings.json")
        with open(self.settings, "w") as fh:
            json.dump(SETTINGS, fh)
        self.env = {**os.environ, "HOME": self.home}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text, name="FIX-THING-01.plan.md"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", newline="") as fh:
            fh.write(text)
        return path

    def check(self, *paths, settings=True):
        argv = [CHECK]
        if settings:
            argv += ["--settings", self.settings]
        proc = subprocess.run(argv + list(paths), capture_output=True, text=True,
                              timeout=10, env=self.env, cwd=self.tmp.name)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

    def test_allowed_commands_pass(self):
        code, out, _ = self.check(self.write(plan("go test ./...\ngo test -race ./...\nmake test-e2e")))
        self.assertEqual(code, 0)
        self.assertEqual(out, "PASS  FIX-THING-01")

    def test_denied_scratch_copy_fails(self):
        # The 2026-10-30 stop: a scratch copy made with rsync, which the deny
        # list blocks in every permission mode.
        code, out, _ = self.check(self.write(plan(
            "mkdir -p /tmp/x/sens && rsync -a --exclude .git ./ /tmp/x/sens/")))
        self.assertEqual(code, 1)
        self.assertIn("denied by Bash(rsync *)", out)
        self.assertIn("rsync -a --exclude .git ./ /tmp/x/sens/", out)

    def test_cp_scratch_copy_passes(self):
        code, _, _ = self.check(self.write(plan("mkdir -p /tmp/x/sens && cp -R . /tmp/x/sens/")))
        self.assertEqual(code, 0)

    def test_ask_rule_fails(self):
        # An ask rule prompts even in auto mode; nobody is there to answer.
        code, out, _ = self.check(self.write(plan("ls -la /usr/bin/env")))
        self.assertEqual(code, 1)
        self.assertIn("prompts (ask rule)", out)

    def test_shell_fences_outside_commands_are_checked(self):
        extra = "\n```bash\ngit commit -m wip\n```\n"
        code, out, _ = self.check(self.write(plan("go test ./...", extra=extra)))
        self.assertEqual(code, 1)
        self.assertIn("Bash(git commit *)", out)

    def test_non_shell_fences_are_ignored(self):
        extra = "\n```text\nrsync is denied, use cp -R\n```\n\n```yaml\nbaseline: abc\n```\n"
        code, _, _ = self.check(self.write(plan("go test ./...", extra=extra)))
        self.assertEqual(code, 0)

    def test_compound_and_substitution_parts_are_checked(self):
        cases = {
            "pipe": "go test ./... | nc host 9",
            "semicolon": "true; rsync a b",
            "or": "false || rsync a b",
            "subshell": "(cd /tmp && rsync a b)",
            "dollar-paren": "echo $(rsync a b)",
            "dollar-paren in quotes": 'echo "$(rsync a b)"',
            "backticks": "echo `rsync a b`",
            "env prefix": "RSYNC_RSH=ssh rsync a b",
            "continuation": "rsync \\\n  -a a b",
        }
        for name, command in cases.items():
            with self.subTest(name):
                code, out, _ = self.check(self.write(plan(command)))
                self.assertEqual(code, 1, out)
                self.assertIn("denied", out)

    def test_quoted_separators_do_not_split(self):
        cases = ["grep -E 'a|rsync b' file", 'grep -c "x; rsync y" file', "printf '%s\\n' 'a && rsync'"]
        for command in cases:
            with self.subTest(command):
                code, out, _ = self.check(self.write(plan(command)))
                self.assertEqual(code, 0, out)

    def test_bare_command_matches_trailing_wildcard_rule(self):
        code, _, _ = self.check(self.write(plan("rsync")))
        self.assertEqual(code, 1)

    def test_word_boundary_is_respected(self):
        code, _, _ = self.check(self.write(plan("rsyncfoo --version")))
        self.assertEqual(code, 0)

    def test_legacy_prefix_rule(self):
        code, out, _ = self.check(self.write(plan("npm publish --dry-run")))
        self.assertEqual(code, 1)
        self.assertIn("Bash(npm publish:*)", out)

    def test_home_spellings_match_tilde_rules(self):
        for command in ["cat $HOME/.ssh/id_rsa", "cat ${HOME}/.ssh/id_rsa", "cat %s/.ssh/id_rsa" % "HOMEDIR"]:
            command = command.replace("HOMEDIR", self.home)
            with self.subTest(command):
                code, out, _ = self.check(self.write(plan(command)))
                self.assertEqual(code, 1, out)

    def test_unattended_no_fails_with_reason(self):
        code, out, _ = self.check(self.write(plan("go test ./...", unattended="no — needs the staging cluster")))
        self.assertEqual(code, 1)
        self.assertIn("declared `unattended: no` — needs the staging cluster", out)

    def test_unattended_missing_fails(self):
        # Plans written before loop-safety existed must be named, not assumed safe.
        code, out, _ = self.check(self.write(plan("go test ./...", unattended=None)))
        self.assertEqual(code, 1)
        self.assertIn("no `unattended:`", out)

    def test_unattended_bad_value_fails(self):
        code, out, _ = self.check(self.write(plan("go test ./...", unattended="maybe")))
        self.assertEqual(code, 1)
        self.assertIn("must be `yes` or `no", out)

    def test_missing_commands_section_fails(self):
        # The 2026-10-30 plan described its gate in prose; nothing named the command.
        code, out, _ = self.check(self.write(plan(None)))
        self.assertEqual(code, 1)
        self.assertIn("no `## Commands` section", out)

    def test_empty_commands_section_fails(self):
        code, out, _ = self.check(self.write(plan("# nothing yet")))
        self.assertEqual(code, 1)
        self.assertIn("lists no commands", out)

    def test_crlf_plan(self):
        text = plan("go test ./...").replace("\n", "\r\n")
        code, out, _ = self.check(self.write(text))
        self.assertEqual(code, 0, out)

    def test_id_falls_back_to_filename(self):
        text = plan("go test ./...").replace("id: FIX-THING-01\n", "")
        code, out, _ = self.check(self.write(text, name="DOCS-X-02.plan.md"))
        self.assertEqual(out, "PASS  DOCS-X-02")

    def test_several_plans_report_each(self):
        good = self.write(plan("go test ./..."), name="A.plan.md")
        bad = self.write(plan("rsync a b").replace("FIX-THING-01", "B-01"), name="B.plan.md")
        code, out, _ = self.check(good, bad)
        self.assertEqual(code, 1)
        self.assertIn("PASS  FIX-THING-01", out)
        self.assertIn("FAIL  B-01", out)

    def test_missing_plan_file_fails(self):
        code, out, _ = self.check(os.path.join(self.tmp.name, "NOPE.plan.md"))
        self.assertEqual(code, 1)
        self.assertIn("cannot read plan", out)

    def test_bad_settings_is_a_data_error(self):
        with open(self.settings, "w") as fh:
            fh.write("{not json")
        code, _, err = self.check(self.write(plan("go test ./...")))
        self.assertEqual(code, 65)
        self.assertIn("cannot read settings", err)

    def test_blanket_bash_deny_fails_everything(self):
        with open(self.settings, "w") as fh:
            json.dump({"permissions": {"deny": ["Bash"]}}, fh)
        code, _, _ = self.check(self.write(plan("go test ./...")))
        self.assertEqual(code, 1)

    def test_default_settings_come_from_home(self):
        os.makedirs(os.path.join(self.home, ".claude"))
        with open(os.path.join(self.home, ".claude", "settings.json"), "w") as fh:
            json.dump(SETTINGS, fh)
        code, out, _ = self.check(self.write(plan("rsync a b")), settings=False)
        self.assertEqual(code, 1)
        self.assertIn("~/.claude/settings.json", out)

    def test_usage_errors(self):
        for argv in ([], ["--settings"], ["--bogus", "x.plan.md"]):
            with self.subTest(argv=argv):
                proc = subprocess.run([CHECK] + argv, capture_output=True, text=True, timeout=10)
                self.assertEqual(proc.returncode, 64)


if __name__ == "__main__":
    unittest.main()
