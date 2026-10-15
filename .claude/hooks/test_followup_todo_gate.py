"""Tests for followup-todo-gate.py, run through its real stdin/stdout contract.

Run: python3 -m unittest discover -s .claude/hooks -p 'test_*.py'
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "followup-todo-gate.py")


def run(payload):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, HOOK], input=raw, capture_output=True, text=True, timeout=10
    )
    return proc.returncode, proc.stdout.strip()


def blocked(msg, **extra):
    code, out = run({"last_assistant_message": msg, **extra})
    assert code == 0, code
    return bool(out) and json.loads(out)["decision"] == "block"


class FollowupTodoGate(unittest.TestCase):
    def test_blocks_left_for_you_without_id(self):
        self.assertTrue(blocked(
            "Done.\n\nLeft for you: orderwand still defaults -es-host to localhost."
        ))

    def test_blocks_open_decisions_without_id(self):
        self.assertTrue(blocked("Open decisions:\n- keep the old flag or drop it"))

    def test_passes_when_id_in_same_paragraph(self):
        self.assertFalse(blocked("Left for you: es-host default, tracked as FIX-ESHOST-01."))

    def test_passes_heading_followed_by_id_list(self):
        self.assertFalse(blocked(
            "Left for you:\n\n- es-host default (FIX-ESHOST-01)\n- stale counts (DOCS-STALE-COUNT-01)"
        ))

    def test_one_id_does_not_excuse_another_untracked_paragraph(self):
        self.assertTrue(blocked(
            "Fixed it, tracked the doc gap as DOCS-LINT-01.\n\n"
            "Something else.\n\n"
            "Worth a follow-up: the retry loop has no backoff."
        ))

    def test_passes_without_deferral_wording(self):
        self.assertFalse(blocked("Updated the template and reassembled CLAUDE.md."))

    def test_ignores_deferral_inside_code_fence(self):
        self.assertFalse(blocked("Example:\n\n```text\nLeft for you: x\n```\n\nAll done."))

    def test_ignores_deferral_inside_blockquote(self):
        self.assertFalse(blocked("The rule says:\n\n> Left for you items must be tracked.\n\nDone."))

    def test_ignores_quoted_mentions_of_phrases(self):
        self.assertFalse(blocked('It flags "left for you" and `open decisions` wording.'))

    def test_unquoted_use_next_to_quoted_text_still_blocks(self):
        self.assertTrue(blocked('Left for you: rename "foo" to `bar`.'))

    def test_bare_revisit_noun_does_not_block(self):
        self.assertFalse(blocked("Staleness accrues when nothing forces a revisit."))

    def test_revisit_later_blocks(self):
        self.assertTrue(blocked("We should revisit this once the API settles."))

    def test_stop_hook_active_never_blocks(self):
        self.assertFalse(blocked("Left for you: x", stop_hook_active=True))

    def test_subagent_never_blocks(self):
        self.assertFalse(blocked("Left for you: x", agent_id="abc", agent_type="Explore"))

    def test_malformed_json_fails_open(self):
        self.assertEqual(run("{not json"), (0, ""))

    def test_missing_transcript_fails_open(self):
        self.assertEqual(run({"transcript_path": "/nonexistent/t.jsonl"}), (0, ""))

    def test_reads_final_message_from_transcript(self):
        entries = [
            {"type": "user", "message": {"content": "do it"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Done."}]}},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "Open questions: should we drop the flag?"}]}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
            fh.write("\n".join(json.dumps(e) for e in entries))
        try:
            code, out = run({"transcript_path": fh.name})
        finally:
            os.unlink(fh.name)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_transcript_earlier_turn_is_ignored(self):
        entries = [
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Left for you: x"}]}},
            {"type": "user", "message": {"content": "next"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "All done."}]}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
            fh.write("\n".join(json.dumps(e) for e in entries))
        try:
            self.assertEqual(run({"transcript_path": fh.name}), (0, ""))
        finally:
            os.unlink(fh.name)


if __name__ == "__main__":
    unittest.main()
