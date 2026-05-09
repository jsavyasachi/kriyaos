import json
import os
import tempfile
import unittest
from unittest.mock import patch

from kriya.grocery_sync import format_grocery_sync_result, plan_grocery_sync, run_grocery_sync


def keep_list(*items):
    return {
        "name": "notes/groceries",
        "title": "Groceries",
        "updated": "2026-05-09T10:00:00Z",
        "items": list(items),
    }


def item(title, completed=False, updated="2026-05-09T10:00:00Z", uid=None):
    data = {"title": title, "completed": completed, "updated": updated}
    if uid:
        data["uid"] = uid
    return data


class TestGrocerySync(unittest.TestCase):
    def test_google_item_missing_in_apple_creates_apple(self):
        actions = plan_grocery_sync(keep_list(item("Milk")), [])

        self.assertEqual(actions, [{"type": "create_apple", "source": "google", "item": {"title": "Milk", "completed": False}}])

    def test_google_completed_item_completes_apple_when_google_newer(self):
        actions = plan_grocery_sync(
            keep_list(item("Milk", completed=True, updated="2026-05-09T11:00:00Z")),
            [item("Milk", completed=False, updated="2026-05-09T10:00:00Z", uid="a1")],
        )

        self.assertEqual(actions, [{"type": "complete_apple", "source": "google", "uid": "a1"}])

    def test_apple_newer_change_queues_google_replacement(self):
        actions = plan_grocery_sync(
            keep_list(item("Milk", completed=False, updated="2026-05-09T10:00:00Z")),
            [item("Milk", completed=True, updated="2026-05-09T11:00:00Z", uid="a1")],
        )

        self.assertEqual(actions, [{"type": "replace_google", "source": "apple"}])

    @patch("kriya.grocery_sync.add_reminder", return_value="apple-new")
    @patch("kriya.grocery_sync.get_reminders_for_list", return_value=[])
    @patch("kriya.grocery_sync.get_grocery_items", return_value=keep_list(item("Milk")))
    def test_run_grocery_sync_applies_apple_create(self, _google, _apple, mock_add):
        with tempfile.TemporaryDirectory() as state_dir:
            result = run_grocery_sync(state_dir=state_dir)

        self.assertFalse(result["aborted"])
        self.assertEqual(result["apple_results"], [{"type": "create_apple", "uid": "apple-new"}])
        mock_add.assert_called_once_with("Groceries", "Milk")

    @patch("kriya.grocery_sync.get_reminders_for_list")
    @patch("kriya.grocery_sync.get_grocery_items", return_value=keep_list(item("Milk")))
    def test_run_grocery_sync_queues_keep_replacement(self, _google, mock_apple):
        mock_apple.return_value = [item("Milk", uid="a1"), item("Eggs", uid="a2")]

        with tempfile.TemporaryDirectory() as state_dir:
            result = run_grocery_sync(state_dir=state_dir)
            with open(result["queued_google"][0], encoding="utf-8") as f:
                pending = json.load(f)

        self.assertEqual(pending["tool"], "keep.replace_note")
        self.assertEqual(pending["args"]["name"], "notes/groceries")
        self.assertEqual([item["title"] for item in pending["args"]["items"]], ["Milk", "Eggs"])

    @patch("kriya.grocery_sync.get_reminders_for_list", return_value=[item(f"Item {i}", uid=f"a{i}") for i in range(3)])
    @patch("kriya.grocery_sync.get_grocery_items", return_value=keep_list())
    def test_run_grocery_sync_circuit_breaker_writes_review_item(self, _google, _apple):
        with tempfile.TemporaryDirectory() as state_dir:
            result = run_grocery_sync(state_dir=state_dir, action_limit=0)
            plan_exists = os.path.exists(result["pending_plan"])
            with open(result["pending_review"], encoding="utf-8") as f:
                pending = json.load(f)

        self.assertTrue(result["aborted"])
        self.assertTrue(plan_exists)
        self.assertEqual(pending["tool"], "sync.review")

    def test_format_grocery_sync_result(self):
        content = format_grocery_sync_result(
            {"aborted": False, "action_count": 2, "apple_results": [{"type": "create_apple"}], "queued_google": ["x"]}
        )

        self.assertIn("Grocery sync complete: 2 planned actions", content)
        self.assertIn("- apple writes: 1", content)
        self.assertIn("- queued google writes: 1", content)


if __name__ == "__main__":
    unittest.main()
