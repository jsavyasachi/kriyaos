import tempfile
import unittest

from kriya.approvals import (
    approve_action,
    create_pending_action,
    format_pending_actions,
    list_by_status,
    list_pending_actions,
    make_idempotency_key,
    reject_action,
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

    def test_list_by_status_filters_items(self):
        with tempfile.TemporaryDirectory() as state_dir:
            first = create_pending_action("tasks.insert", {"title": "Reply"}, "r", "s1", "i", state_dir)
            second = create_pending_action("tasks.insert", {"title": "Call"}, "r", "s2", "i", state_dir)
            approve_action(first.rsplit("/", 1)[-1].removesuffix(".json"), state_dir)
            reject_action(second.rsplit("/", 1)[-1].removesuffix(".json"), state_dir)

            approved = list_by_status("approved", state_dir)
            rejected = list_by_status("rejected", state_dir)

        self.assertEqual([item["args"]["title"] for item in approved], ["Reply"])
        self.assertEqual([item["args"]["title"] for item in rejected], ["Call"])
