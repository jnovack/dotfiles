"""Tests for agent-watchdog and claude-permission-mode, run as real processes.

Run: python3 -m unittest discover -s .claude/bin -p 'test_*.py'
"""
import os
import subprocess
import tempfile
import threading
import time
import unittest

BIN = os.path.dirname(os.path.abspath(__file__))
WATCHDOG = os.path.join(BIN, "agent-watchdog")
MODE = os.path.join(BIN, "claude-permission-mode")


def run(argv, env=None, timeout=10):
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


class AgentWatchdog(unittest.TestCase):
    """Lays out a session the way Claude Code does: tasks/<id>.output is a
    symlink to subagents/agent-<id>.jsonl, with agent-<id>.meta.json beside it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        os.makedirs(os.path.join(root, "subagents"))
        os.makedirs(os.path.join(root, "tasks"))
        self.transcript = os.path.join(root, "subagents", "agent-a1.jsonl")
        self.meta = os.path.join(root, "subagents", "agent-a1.meta.json")
        self.output = os.path.join(root, "tasks", "a1.output")
        with open(self.transcript, "w") as fh:
            fh.write("{}\n")
        os.symlink(self.transcript, self.output)

    def tearDown(self):
        self.tmp.cleanup()

    def write_meta(self, finished):
        with open(self.meta, "w") as fh:
            fh.write('{"agentType":"general-purpose","finished":%s}' % ("true" if finished else "false"))

    def age_transcript(self, seconds):
        past = time.time() - seconds
        os.utime(self.transcript, (past, past))

    def test_finished_agent_exits_zero(self):
        self.write_meta(True)
        code, out, _ = run([WATCHDOG, self.output, "1200", "1"])
        self.assertEqual(code, 0)
        self.assertIn("finished", out)

    def test_silent_running_agent_is_stalled(self):
        # The 2026-10-21 failure: an agent blocked on a permission prompt
        # writes nothing and never sets finished.
        self.write_meta(False)
        self.age_transcript(600)
        code, out, _ = run([WATCHDOG, self.output, "300", "1"])
        self.assertEqual(code, 2)
        self.assertIn("stalled", out)

    def test_finished_beats_silence(self):
        # A finished agent is silent too; reporting it as stalled would page
        # the operator for nothing.
        self.write_meta(True)
        self.age_transcript(600)
        code, out, _ = run([WATCHDOG, self.output, "300", "1"])
        self.assertEqual(code, 0)

    def test_stalled_without_meta_file(self):
        self.age_transcript(600)
        code, _, _ = run([WATCHDOG, self.output, "300", "1"])
        self.assertEqual(code, 2)

    def test_keeps_waiting_while_active_then_reports_finish(self):
        self.write_meta(False)

        def finish_later():
            time.sleep(1.5)
            self.write_meta(True)

        t = threading.Thread(target=finish_later)
        t.start()
        code, out, _ = run([WATCHDOG, self.output, "1200", "1"])
        t.join()
        self.assertEqual(code, 0)
        self.assertIn("finished", out)

    def test_plain_file_path_is_accepted(self):
        self.write_meta(True)
        code, _, _ = run([WATCHDOG, self.transcript, "1200", "1"])
        self.assertEqual(code, 0)

    def test_missing_transcript(self):
        code, _, err = run([WATCHDOG, os.path.join(self.tmp.name, "nope.jsonl"), "1200", "1"])
        self.assertEqual(code, 66)
        self.assertIn("missing", err)

    def test_dangling_symlink_is_missing(self):
        os.remove(self.transcript)
        code, _, _ = run([WATCHDOG, self.output, "1200", "1"])
        self.assertEqual(code, 66)

    def test_usage_errors(self):
        for argv in ([], [self.output, "x"], [self.output, "10", "1.5"], [self.output, "1", "2", "3"]):
            with self.subTest(argv=argv):
                code, _, _ = run([WATCHDOG, *argv])
                self.assertEqual(code, 64)


class ClaudePermissionMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        self.slug = "-Users-x-repo"
        self.session = "0f0f-session"
        self.scratchpad = os.path.join(self.tmp.name, "claude-501", self.slug, self.session, "scratchpad")
        os.makedirs(self.scratchpad)
        self.projects = os.path.join(self.home, ".claude", "projects", self.slug)
        os.makedirs(self.projects)
        self.env = {**os.environ, "HOME": self.home}

    def tearDown(self):
        self.tmp.cleanup()

    def write_transcript(self, lines):
        with open(os.path.join(self.projects, self.session + ".jsonl"), "w") as fh:
            fh.write("\n".join(lines) + "\n")

    def mode(self, scratchpad=None):
        code, out, _ = run([MODE, scratchpad or self.scratchpad], env=self.env)
        self.assertEqual(code, 0)
        return out

    def test_reports_most_recent_mode(self):
        self.write_transcript([
            '{"type":"user","permissionMode":"acceptEdits"}',
            '{"type":"assistant"}',
            '{"type":"user","permissionMode":"auto"}',
        ])
        self.assertEqual(self.mode(), "auto")

    def test_trailing_slash_on_scratchpad(self):
        self.write_transcript(['{"type":"user","permissionMode":"bypassPermissions"}'])
        self.assertEqual(self.mode(self.scratchpad + "/"), "bypassPermissions")

    def test_unknown_without_transcript(self):
        self.assertEqual(self.mode(), "unknown")

    def test_unknown_when_field_absent(self):
        # The transcript format is internal; a rename must degrade to unknown,
        # never to a wrong mode.
        self.write_transcript(['{"type":"user","mode":"auto"}'])
        self.assertEqual(self.mode(), "unknown")

    def test_usage_error(self):
        code, _, _ = run([MODE], env=self.env)
        self.assertEqual(code, 64)


if __name__ == "__main__":
    unittest.main()
