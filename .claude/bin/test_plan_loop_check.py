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


FENCE = "```"


def phase_block(n, unattended="yes", commands="go test ./...", step_extra="", tail="",
                commands_section=None, start=True, end=True):
    """One marker-delimited refactor phase. `commands` is the body of the bash
    fence under ### Commands (None omits the section); `commands_section`
    replaces that whole section. Nothing here is executed: it is checker input."""
    out = ""
    if start:
        out += "<!-- phase:%s:start -->\n\n" % n
    out += "## Phase %s — Subject\n\n**Depends on:** —\n**Model:** Sonnet\n" % n
    if unattended is not None:
        out += "**Unattended:** %s\n" % unattended
    out += "**Baseline:** —\n\n### Standard Preamble\n\nRead AGENTS.md.\n\n"
    out += "### Step Index\n\n| Step | Description | Status |\n| --- | --- | --- |\n"
    out += "| %s.a | Do it | Not started |\n\n### Step %s.a — Do it\n\nEdit the file.\n" % (n, n)
    out += step_extra
    if commands_section is not None:
        out += "\n" + commands_section
    elif commands is not None:
        out += "\n### Commands\n\n%sbash\n%s\n%s\n" % (FENCE, commands, FENCE)
    out += "\n### Definition of Done\n\n- [ ] Tests pass\n" + tail
    if end:
        out += "\n<!-- phase:%s:end -->\n" % n
    return out


def neighbor(n):
    """A different phase that is unsafe on every count, to prove isolation."""
    return phase_block(n, unattended="no — operator", commands="rsync a b",
                       step_extra="\n%sbash\ngit commit -m wip\n%s\n" % (FENCE, FENCE))


def phase_doc(*blocks):
    head = ("# Refactor: Thing\n\n<!-- shared:intent:start -->\n\n## Intent\n\nWords.\n\n"
            "<!-- shared:intent:end -->\n\n## Test Command\n\n    go test ./...\n\n---\n\n")
    return head + "\n---\n\n".join(blocks)


def with_neighbors(block, n=2):
    return phase_doc(neighbor(n - 1), block, neighbor(n + 1))


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

    def check(self, *paths, settings=True, phase=None):
        argv = [CHECK]
        if settings:
            argv += ["--settings", self.settings]
        if phase is not None:
            argv += ["--phase", str(phase)]
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

    # ---- phase mode (--phase N): one marker-delimited refactor phase ----

    def phase_file(self, text, name="REFACTOR.thing.md"):
        return self.write(text, name=name)

    def phase_check(self, block, n=2, **kw):
        return self.check(self.phase_file(with_neighbors(block, n)), phase=n, **kw)  # noqa

    def test_phase_safe_passes_and_ignores_unsafe_neighbors(self):
        code, out, _ = self.phase_check(phase_block(2))
        self.assertEqual((code, out), (0, "PASS  thing#2"))

    def test_phase_report_ids(self):
        text = phase_doc(phase_block(2))
        cases = {"REFACTOR.thing.md": "thing#2", "REFACTOR.thing.completed.md": "thing#2",
                 "plain.md": "plain#2", "notes.txt": "notes#2", "bare": "bare#2"}
        for name, want in cases.items():
            with self.subTest(name):
                code, out, _ = self.check(self.phase_file(text, name=name), phase=2)
                self.assertEqual((code, out), (0, "PASS  " + want))

    def test_phase_exact_number_one_versus_ten(self):
        text = phase_doc(phase_block(10, commands="rsync a b"), phase_block(1))
        code, out, _ = self.check(self.phase_file(text), phase=1)
        self.assertEqual((code, out), (0, "PASS  thing#1"))
        code, out, _ = self.check(self.phase_file(text), phase=10)
        self.assertEqual(code, 1)
        self.assertIn("denied by Bash(rsync *)", out)

    def test_phase_unattended_missing_fails_with_guidance(self):
        code, out, _ = self.phase_check(phase_block(2, unattended=None))
        self.assertEqual(code, 1)
        self.assertIn("FAIL  thing#2", out)
        self.assertIn("**Unattended:**", out)
        self.assertIn("### Commands", out)

    def test_phase_unattended_no_fails_with_reason(self):
        code, out, _ = self.phase_check(phase_block(2, unattended="no — final phase needs the operator"))
        self.assertEqual(code, 1)
        self.assertIn("declared `unattended: no` — final phase needs the operator", out)

    def test_phase_unattended_bad_value_fails(self):
        code, out, _ = self.phase_check(phase_block(2, unattended="maybe"))
        self.assertEqual(code, 1)
        self.assertIn("must be `yes` or `no", out)

    def test_phase_unattended_duplicate_fails(self):
        block = phase_block(2).replace("**Baseline:** —\n", "**Unattended:** yes\n**Baseline:** —\n")
        code, out, _ = self.phase_check(block)
        self.assertEqual(code, 1)
        self.assertIn("more than one", out)

    def test_phase_unattended_in_fence_does_not_opt_in(self):
        extra = "\n%stext\n**Unattended:** yes\n%s\n" % (FENCE, FENCE)
        code, out, _ = self.phase_check(phase_block(2, unattended=None, step_extra=extra))
        self.assertEqual(code, 1)
        self.assertIn("no `**Unattended:**`", out)

    def test_phase_unattended_outside_header_fails(self):
        code, out, _ = self.phase_check(phase_block(2, unattended=None, step_extra="\n**Unattended:** yes\n"))
        self.assertEqual(code, 1)
        self.assertIn("phase header", out)

    def test_phase_commands_missing_fails(self):
        code, out, _ = self.phase_check(phase_block(2, commands=None))
        self.assertEqual(code, 1)
        self.assertIn("no `### Commands`", out)

    def test_phase_commands_comment_only_fails(self):
        code, out, _ = self.phase_check(phase_block(2, commands="# nothing yet\n"))
        self.assertEqual(code, 1)
        self.assertIn("lists no commands", out)

    def test_phase_commands_heading_in_fence_does_not_count(self):
        extra = "\n````text\n### Commands\n%sbash\ngo test ./...\n%s\n````\n" % (FENCE, FENCE)
        code, out, _ = self.phase_check(phase_block(2, commands=None, step_extra=extra))
        self.assertEqual(code, 1)
        self.assertIn("no `### Commands`", out)

    def test_phase_commands_wrong_level_does_not_count(self):
        section = "## Commands\n\n%sbash\ngo test ./...\n%s\n" % (FENCE, FENCE)
        code, out, _ = self.phase_check(phase_block(2, commands_section=section))
        self.assertEqual(code, 1)
        self.assertIn("no `### Commands`", out)

    def test_phase_commands_duplicate_fails(self):
        section = ("### Commands\n\n%sbash\ngo test ./...\n%s\n\n### Commands\n\n%sbash\nmake\n%s\n"
                   % (FENCE, FENCE, FENCE, FENCE))
        code, out, _ = self.phase_check(phase_block(2, commands_section=section))
        self.assertEqual(code, 1)
        self.assertIn("more than one `### Commands`", out)

    def test_phase_neighbor_commands_do_not_satisfy_selected_phase(self):
        text = phase_doc(phase_block(1), phase_block(2, commands=None))
        code, out, _ = self.check(self.phase_file(text), phase=2)
        self.assertEqual(code, 1)
        self.assertIn("no `### Commands`", out)

    def test_phase_commands_section_ends_at_levels_one_to_three(self):
        for heading in ("# Top", "## Other", "### Notes"):
            with self.subTest(heading):
                section = ("### Commands\n\n%s\n\n%s\n\n%sbash\ngo test ./...\n%s\n"
                           % ("Prose only.", heading, FENCE, FENCE))
                code, out, _ = self.phase_check(phase_block(2, commands_section=section))
                self.assertEqual(code, 1, out)
                self.assertIn("lists no commands", out)

    def test_phase_commands_section_includes_level_four(self):
        section = "### Commands\n\n#### Validation\n\n%sbash\ngo test ./...\n%s\n" % (FENCE, FENCE)
        code, out, _ = self.phase_check(phase_block(2, commands_section=section))
        self.assertEqual(code, 0, out)

    def test_phase_policy_scans_every_shell_fence(self):
        fence = lambda body: "\n%sbash\n%s\n%s\n" % (FENCE, body, FENCE)
        cases = {
            "commands": dict(commands="go test ./...\nrsync a b"),
            "step": dict(step_extra=fence("rsync a b")),
            "notes": dict(tail="\n### Notes\n" + fence("rsync a b")),
            "corrections": dict(tail="\n### Corrections\n" + fence("git commit -m x")),
        }
        for name, kw in cases.items():
            with self.subTest(name):
                code, out, _ = self.phase_check(phase_block(2, **kw))
                self.assertEqual(code, 1, out)
                self.assertIn("denied by", out)

    def test_phase_ask_rule_fails(self):
        code, out, _ = self.phase_check(phase_block(2, commands="ls /usr/bin/env"))
        self.assertEqual(code, 1)
        self.assertIn("prompts (ask rule)", out)

    def test_phase_non_shell_fences_are_ignored(self):
        extra = "\n%stext\nrsync is denied\n%s\n\n%syaml\nrun: rsync a b\n%s\n" % ((FENCE,) * 4)
        code, out, _ = self.phase_check(phase_block(2, step_extra=extra))
        self.assertEqual(code, 0, out)

    def test_phase_shell_semantics_are_preserved(self):
        bad = ["true; rsync a b", "echo $(rsync a b)", "echo `rsync a b`", "rsync \\\n  -a a b",
               "RSYNC_RSH=ssh rsync a b"]
        for command in bad:
            with self.subTest(command):
                code, out, _ = self.phase_check(phase_block(2, commands="go test ./...\n" + command))
                self.assertEqual(code, 1, out)
        code, out, _ = self.phase_check(phase_block(2, commands="grep -E 'a|rsync b' file"))
        self.assertEqual(code, 0, out)

    def test_phase_crlf(self):
        text = with_neighbors(phase_block(2)).replace("\n", "\r\n")
        code, out, _ = self.check(self.phase_file(text), phase=2)
        self.assertEqual((code, out), (0, "PASS  thing#2"))

    def test_phase_markers_in_fenced_examples_are_ignored(self):
        example = "%stext\n<!-- phase:2:start -->\nrsync a b\n<!-- phase:2:end -->\n%s\n" % (FENCE * 2, FENCE * 2)
        text = phase_doc(example, phase_block(2))
        code, out, _ = self.check(self.phase_file(text), phase=2)
        self.assertEqual((code, out), (0, "PASS  thing#2"))

    def test_phase_malformed_markers_fail_closed(self):
        cases = {
            "missing": phase_doc(phase_block(1)),
            "no end": phase_doc(phase_block(2, end=False)),
            "no start": phase_doc(phase_block(2, start=False)),
            "reversed": phase_doc("<!-- phase:2:end -->\n\n" + phase_block(2, start=False, end=False)
                                  + "\n<!-- phase:2:start -->\n"),
            "duplicate": phase_doc(phase_block(2), phase_block(2)),
            "nested": phase_doc(phase_block(2, end=False) + phase_block(3) + "\n<!-- phase:2:end -->\n"),
        }
        for name, text in cases.items():
            with self.subTest(name):
                code, out, _ = self.check(self.phase_file(text), phase=2)
                self.assertEqual(code, 1, out)
                self.assertIn("FAIL  thing#2", out)
                self.assertIn("marker", out)

    def test_phase_cli_rejects_bad_phase_arguments(self):
        path = self.phase_file(phase_doc(phase_block(2)))
        for argv in (["--phase"], ["--phase", "0"], ["--phase", "-1"], ["--phase", "1.5"],
                     ["--phase", "abc"], ["--phase", "2", "--phase", "2"], ["--phase", "2"]):
            with self.subTest(argv=argv):
                args = argv + ([path] if argv != ["--phase", "2"] else [])
                proc = subprocess.run([CHECK, "--settings", self.settings] + args,
                                      capture_output=True, text=True, timeout=10)
                self.assertEqual(proc.returncode, 64)

    def test_phase_flag_order_and_default_settings(self):
        path = self.phase_file(with_neighbors(phase_block(2)))
        proc = subprocess.run([CHECK, "--phase", "2", "--settings", self.settings, path],
                              capture_output=True, text=True, timeout=10, env=self.env)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "PASS  thing#2"))
        os.makedirs(os.path.join(self.home, ".claude"))
        with open(os.path.join(self.home, ".claude", "settings.json"), "w") as fh:
            json.dump(SETTINGS, fh)
        unsafe = self.phase_file(phase_doc(phase_block(2, commands="rsync a b")), name="REFACTOR.u.md")
        code, out, _ = self.check(unsafe, phase=2, settings=False)
        self.assertEqual(code, 1)
        self.assertIn("~/.claude/settings.json", out)

    def test_phase_bad_settings_is_a_data_error(self):
        with open(self.settings, "w") as fh:
            fh.write("{not json")
        code, _, err = self.phase_check(phase_block(2))
        self.assertEqual(code, 65)
        self.assertIn("cannot read settings", err)

    def test_phase_missing_file_and_multiple_inputs(self):
        good = self.phase_file(phase_doc(phase_block(2)), name="REFACTOR.good.md")
        bad = self.phase_file(phase_doc(phase_block(2, commands="rsync a b")), name="REFACTOR.bad.md")
        gone = os.path.join(self.tmp.name, "REFACTOR.gone.md")
        code, out, _ = self.check(good, bad, gone, phase=2)
        self.assertEqual(code, 1)
        self.assertIn("PASS  good#2", out)
        self.assertIn("FAIL  bad#2  denied by Bash(rsync *)", out)
        self.assertIn("FAIL  gone#2  cannot read plan", out)
        code, out, _ = self.check(good, phase=2)
        self.assertEqual(code, 0)

    def test_phase_mode_does_not_change_file_mode(self):
        code, out, _ = self.check(self.write(plan("go test ./...")))
        self.assertEqual((code, out), (0, "PASS  FIX-THING-01"))


if __name__ == "__main__":
    unittest.main()
