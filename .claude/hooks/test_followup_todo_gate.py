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

    # --- FIX-FOLLOWUP-01: negated and completed-fix phrases are not deferrals ---

    INCIDENT_2 = (
        "The reviewer found four low-severity issues and I fixed all four. "
        "The reviewer marked two of them out of scope, but I fixed them here anyway:"
    )

    def test_negated_follow_up_does_not_block(self):
        # 2026-11-10 incident 1: a four-bullet summary (one paragraph to the
        # hook) ending in a sentence that reports nothing was deferred.
        plan = (
            "- Added the exemption helpers.\n- Added the tests.\n"
            "- Updated the docstring.\n- Reran the suite.\n"
            "No follow-up TODO was needed."
        )
        for msg in ("No follow-up TODO was needed.", plan, "no FOLLOW-UP needed", "Without a follow-up."):
            with self.subTest(msg=msg):
                self.assertFalse(blocked(msg))

    def test_negated_open_decision_and_scope_do_not_block(self):
        for msg in ("No open decisions remain.", "Nothing is out of scope.",
                    "No additional urgent open decisions remain."):
            with self.subTest(msg=msg):
                self.assertFalse(blocked(msg))

    def test_out_of_scope_already_fixed_does_not_block(self):
        self.assertFalse(blocked(self.INCIDENT_2))

    def test_affirmative_same_work_completion_does_not_block(self):
        verbs = ("fixed", "resolved", "addressed", "handled")
        cases = [
            "The issues were out of scope, but I fixed them here anyway.",
            "The issue was out of scope but is already resolved.",
            "The issue was out of scope, but we have addressed it.",
            "The issue was out of scope but done.",
            "The issue was OUT OF SCOPE,   but is   done here.",
        ]
        for v in verbs:
            cases += [
                f"The issue was out of scope, but I {v} it.",
                f"The issues were out of scope and we have already {v} them here.",
                f"The issue was out of scope, but has been already {v} anyway.",
                f"The issues were out of scope, {v} here anyway.",
                f"The issue was out of scope but was {v}.",
                f"The issues are out of scope and are {v}",
                f"The issues were out of scope, but have been {v} here",
            ]
        for msg in cases:
            with self.subTest(msg=msg):
                self.assertFalse(blocked(msg))

    def test_negated_uncertain_or_future_completion_still_blocks(self):
        for msg in (
            "The issue is out of scope and not fixed.",
            "The issue is out of scope, but I have not fixed it.",
            "The issue is out of scope, but I will fix it.",
            "The issue is out of scope, but I might have fixed it.",
            "The issue is out of scope, but I fixed it if the test passes.",
            "I think the issue was out of scope but fixed.",
            "Maybe the issue was out of scope but is resolved.",
            "The issue was out of scope but is resolved, unless it regresses.",
        ):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_different_or_partial_work_still_blocks(self):
        for msg in (
            "I fixed the typo, but the timeout is out of scope.",
            "The timeout is out of scope, but I fixed the typo.",
            "The issues are out of scope, but I fixed only some of them.",
            "The issues are out of scope, but I fixed them except the timeout.",
        ):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_negated_completion_does_not_negate_deferral(self):
        msgs = ["The issue is not fixed and out of scope."]
        msgs += [f"The issue is not {v} and out of scope."
                 for v in ("fixed", "resolved", "addressed", "handled", "done")]
        for msg in msgs:
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_unnegated_deferrals_still_block(self):
        for msg in (
            "Worth a follow-up: the retry loop has no backoff.",
            "One open decision now sits before Phase 9 runs.",
            "The reviewer marked two of them out of scope.",
        ):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_negation_in_other_clause_does_not_excuse(self):
        for msg in ("No tests failed; open decision: keep the flag?",
                    "I have no time, so left for you: x"):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_dash_or_parenthesis_ends_the_negator_clause(self):
        # Review R-01: a negator before a dash or parenthesis belongs to another
        # clause and must not exempt the deferral after it.
        for msg in ("Nothing breaks — follow-up needed on the retry loop.",
                    "No owner – open question: who owns the retry loop?",
                    "Fixed X without Y — a follow-up is needed.",
                    "Tests pass (no flakes) follow-up: tune the retry."):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_negated_reminder_still_blocks(self):
        # Review R-02: "do not forget" negates the forgetting, not the deferral.
        for msg in ("Do not forget the follow-up on the retry loop.",
                    "We should not skip the follow-up on the timeout.",
                    "Never miss a follow-up here."):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_negation_is_whole_word_and_never_self(self):
        for msg in ("Notes are out of scope.", "Not tracked yet: the retry loop.",
                    "Nothing-burger follow-up is pending.",
                    "No additional urgent pending open decisions remain."):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_negation_after_phrase_does_not_excuse(self):
        self.assertTrue(blocked("A follow-up is needed, with no owner."))

    def test_completion_verb_in_earlier_sentence_does_not_excuse(self):
        self.assertTrue(blocked("I fixed all four. The reviewer marked two of them out of scope."))

    def test_stripped_spans_do_not_excuse(self):
        for msg in ('The "no" follow-up is pending.',
                    "The issue is out of scope, but `I fixed them`."):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

    def test_one_exempt_match_does_not_hide_another_deferral(self):
        for msg in (
            "No follow-up was needed, but a follow-up is pending.",
            "The issue was out of scope but fixed, and the timeout is out of scope.",
            "Nothing is out of scope.\n\nWorth a follow-up: the retry loop.",
            "No follow-up needed.\n\nOpen decisions: keep the flag?",
        ):
            with self.subTest(msg=msg):
                self.assertTrue(blocked(msg))

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
