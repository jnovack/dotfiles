"""Tests for codex-job-status, run as a real process.

Run: python3 -m unittest discover -s .claude/bin -p 'test_*.py'
"""
import os
import subprocess
import tempfile
import unittest

BIN = os.path.dirname(os.path.abspath(__file__))
STATUS = os.path.join(BIN, "codex-job-status")

# Real ERROR lines in the shape `codex exec` prints them (codex-cli 0.164.0).
USAGE_LIMIT = (
    "ERROR: You've hit your usage limit. Upgrade to Pro "
    "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage "
    "to purchase more credits or try again at 3:14 PM."
)
QUOTA = "ERROR: Quota exceeded. Check your plan and billing details."
RETRY_429 = "ERROR: exceeded retry limit, last status: 429 Too Many Requests"


class CodexJobStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.job = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        with open(os.path.join(self.job, name), "w") as fh:
            fh.write(text)

    def run_status(self, *argv):
        proc = subprocess.run(
            [STATUS, *(argv or (self.job,))], capture_output=True, text=True, timeout=10
        )
        return proc.returncode, proc.stdout.strip()

    # --- ok -----------------------------------------------------------------

    def test_zero_exit_with_last_message_is_ok(self):
        self.write("codex-exit.txt", "0\n")
        self.write("codex-last.txt", "Handoff complete.\n")
        self.assertEqual(self.run_status(), (0, "ok"))

    # --- unavailable: the loop fails open on these ----------------------------

    def test_usage_limit_is_unavailable(self):
        self.write("codex-exit.txt", "1\n")
        self.write("codex-out.txt", "codex starting\n" + USAGE_LIMIT + "\n")
        code, out = self.run_status()
        self.assertEqual(code, 2)
        self.assertEqual(out, "unavailable: " + USAGE_LIMIT)

    def test_api_key_quota_is_unavailable(self):
        self.write("codex-exit.txt", "1")
        self.write("codex-out.txt", QUOTA + "\n")
        self.assertEqual(self.run_status()[0], 2)

    def test_rate_limit_past_retries_is_unavailable(self):
        self.write("codex-exit.txt", "1\n")
        self.write("codex-out.txt", RETRY_429 + "\n")
        self.assertEqual(self.run_status()[0], 2)

    # --- failed: everything else still stops the loop -------------------------

    def test_quota_wording_with_zero_exit_is_not_unavailable(self):
        # A run that finished is judged on its own result, never skipped.
        self.write("codex-exit.txt", "0\n")
        self.write("codex-out.txt", USAGE_LIMIT + "\n")
        self.write("codex-last.txt", "done\n")
        self.assertEqual(self.run_status(), (0, "ok"))

    def test_quota_wording_outside_an_error_line_is_failed(self):
        # Codex narrating a file that mentions "usage limit" (this repo's own
        # docs do) must not turn a real failure into a skip.
        self.write("codex-exit.txt", "1\n")
        self.write("codex-out.txt", "reading: You've hit your usage limit\nERROR: boom\n")
        code, out = self.run_status()
        self.assertEqual(code, 1)
        self.assertEqual(out, "failed: codex exited 1")

    def test_other_nonzero_exit_is_failed(self):
        self.write("codex-exit.txt", "1\n")
        self.write("codex-out.txt", "ERROR: stream disconnected before completion\n")
        self.assertEqual(self.run_status(), (1, "failed: codex exited 1"))

    def test_nonzero_exit_without_log_is_failed(self):
        self.write("codex-exit.txt", "127\n")
        self.assertEqual(self.run_status(), (1, "failed: codex exited 127"))

    def test_missing_exit_file_is_failed(self):
        code, out = self.run_status()
        self.assertEqual(code, 1)
        self.assertIn("missing or unreadable", out)

    def test_malformed_exit_files_are_failed(self):
        for text in ("", "\n", "abc", "1 2", "-1", "256", "0255", "1\n2\n"):
            with self.subTest(text=text):
                self.write("codex-exit.txt", text)
                self.write("codex-out.txt", USAGE_LIMIT + "\n")
                code, out = self.run_status()
                self.assertEqual(code, 1)
                self.assertTrue(out.startswith("failed: malformed"), out)

    def test_zero_exit_with_empty_last_message_is_failed(self):
        self.write("codex-exit.txt", "0\n")
        self.write("codex-last.txt", "")
        code, out = self.run_status()
        self.assertEqual(code, 1)
        self.assertIn("missing or empty", out)

    def test_usage_error(self):
        proc = subprocess.run([STATUS], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 64)


if __name__ == "__main__":
    unittest.main()
