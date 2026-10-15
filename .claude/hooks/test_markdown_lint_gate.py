"""Tests for markdown-lint-gate.py, run through its real stdin/stdout contract.

Run: python3 -m unittest discover -s .claude/hooks -p 'test_*.py'
Lint-dependent tests skip when markdownlint-cli2 is not installed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "markdown-lint-gate.py")

CLEAN = "# Title\n\nSome text.\n"
BROKEN = "# Title\nText right under a heading.\n"  # MD022


def run(payload, env=None):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, HOOK], input=raw, capture_output=True, text=True,
        timeout=60, env=env,
    )
    return proc.returncode, proc.stdout.strip()


def have_linter():
    if shutil.which("markdownlint-cli2"):
        return True
    if not shutil.which("npx"):
        return False
    probe = subprocess.run(
        ["npx", "--no-install", "markdownlint-cli2", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    return probe.returncode in (0, 2) and "markdownlint" in (probe.stdout + probe.stderr)


class MarkdownLintGate(unittest.TestCase):
    def setUp(self):
        # Under the repo, not the system temp dir: the hook skips temp paths.
        self.tmp = tempfile.TemporaryDirectory(dir=HERE)
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)
        return path

    def edit(self, path, env=None):
        return run({"tool_name": "Edit", "tool_input": {"file_path": path}}, env)

    @unittest.skipUnless(have_linter(), "markdownlint-cli2 not installed")
    def test_reports_lint_failure(self):
        code, out = self.edit(self.write("doc.md", BROKEN))
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["decision"], "block")
        self.assertIn("MD022", result["reason"])

    @unittest.skipUnless(have_linter(), "markdownlint-cli2 not installed")
    def test_clean_file_is_silent(self):
        self.assertEqual(self.edit(self.write("doc.md", CLEAN)), (0, ""))

    def test_skips_local_tracking_files(self):
        self.assertEqual(self.edit(self.write(".local/TODO.md", BROKEN)), (0, ""))

    def test_skips_non_markdown(self):
        self.assertEqual(self.edit(self.write("notes.txt", BROKEN)), (0, ""))

    def test_missing_file_fails_open(self):
        self.assertEqual(self.edit(os.path.join(self.dir, "gone.md")), (0, ""))

    def test_malformed_json_fails_open(self):
        self.assertEqual(run("{not json"), (0, ""))

    def test_no_linter_fails_open(self):
        env = dict(os.environ, PATH="/nonexistent")
        self.assertEqual(self.edit(self.write("doc.md", BROKEN), env), (0, ""))


if __name__ == "__main__":
    unittest.main()
