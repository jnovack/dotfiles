"""Tests for cron-auto-mode-gate.py, run through its real stdin/stdout contract.

Run: python3 -m unittest discover -s .claude/hooks -p 'test_*.py'
"""
import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cron-auto-mode-gate.py")


def run(payload):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, HOOK], input=raw, capture_output=True, text=True, timeout=10
    )
    return proc.returncode, proc.stdout.strip()


def cron(mode=None, **extra):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "CronCreate",
        "tool_input": {"cron": "21 0 21 10 *", "prompt": "Invoke the todo-loop skill", "recurring": False},
        **extra,
    }
    if mode is not None:
        payload["permission_mode"] = mode
    return payload


def denied(payload):
    code, out = run(payload)
    assert code == 0, code
    if not out:
        return False
    decision = json.loads(out)["hookSpecificOutput"]
    return decision["permissionDecision"] == "deny"


class CronAutoModeGate(unittest.TestCase):
    def test_denies_accept_edits(self):
        # The 2026-10-21 incident: scheduled from an acceptEdits session.
        self.assertTrue(denied(cron("acceptEdits")))

    def test_denies_every_prompting_mode(self):
        for mode in ("default", "acceptEdits", "plan", "dontAsk"):
            with self.subTest(mode=mode):
                self.assertTrue(denied(cron(mode)))

    def test_allows_auto_and_bypass(self):
        for mode in ("auto", "bypassPermissions"):
            with self.subTest(mode=mode):
                self.assertFalse(denied(cron(mode)))

    def test_missing_mode_fails_closed(self):
        self.assertTrue(denied(cron()))
        self.assertTrue(denied(cron("")))

    def test_reason_names_mode_and_fix(self):
        _, out = run(cron("acceptEdits"))
        reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("acceptEdits", reason)
        self.assertIn("--permission-mode auto", reason)

    def test_ignores_other_tools(self):
        payload = cron("acceptEdits", tool_name="Bash")
        self.assertFalse(denied(payload))

    def test_malformed_payload_fails_open(self):
        code, out = run("not json")
        self.assertEqual((code, out), (0, ""))


if __name__ == "__main__":
    unittest.main()
