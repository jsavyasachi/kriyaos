import tempfile
import unittest

from kriya.approvals import (
    create_pending_action,
    format_pending_actions,
    list_pending_actions,
    make_idempotency_key,
)


class TestApprovals(unittest.TestCase):
    def test_make_idempotency_key_is_stable(self):
        first = make_idempotency_key("tasks.insert", "email:1", "reply")
        second = make_idempotency_key("tasks.insert", "email:1", "reply")

        self.assertEqual(first, second)

    def test_create_pending_action_is_idempotent(self):
        with tempfile.TemporaryDirectory() as state_dir:
            first = create_pending_action(
                "tasks.insert",
                {"title": "Reply"},
                "Email looks actionable.",
                "email:1",
                "reply",
                state_dir,
            )
            second = create_pending_action(
                "tasks.insert",
                {"title": "Reply changed"},
                "Different rationale.",
                "email:1",
                "reply",
                state_dir,
            )
            items = list_pending_actions(state_dir)

        self.assertEqual(first, second)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["args"], {"title": "Reply"})

    def test_format_pending_actions(self):
        content = format_pending_actions(
            [
                {
                    "id": "abc",
                    "tool": "tasks.insert",
                    "intent": "Follow up",
                    "rationale": "Email looks actionable.",
                }
            ]
        )

        self.assertIn("**abc** `tasks.insert`: Follow up", content)
