import json
import os
import tempfile
import unittest
from unittest.mock import patch

from kriya.task_sync import format_task_sync_result, run_task_sync


class TestTaskSync(unittest.TestCase):
    @patch("kriya.task_sync.add_reminder", return_value="apple-new")
    @patch("kriya.task_sync.get_reminders_for_sync", return_value=[])
    @patch(
        "kriya.task_sync.get_tasks_for_sync",
        return_value=[
            {
                "id": "g1",
                "title": "File taxes",
                "due": "2026-05-10",
                "notes": "Use report",
                "completed": False,
                "updated": "2026-05-05T10:00:00Z",
            }
        ],
    )
    def test_run_task_sync_applies_apple_create_and_saves_mapping(self, _google, _apple, mock_add):
        with tempfile.TemporaryDirectory() as state_dir:
            result = run_task_sync(state_dir=state_dir)
            with open(result["mappings"], encoding="utf-8") as f:
                mappings = json.load(f)

        self.assertFalse(result["aborted"])
        self.assertEqual(result["apple_results"], [{"type": "create_apple", "uid": "apple-new"}])
        mock_add.assert_called_once_with("Reminders", "File taxes", due="2026-05-10", notes="Use report")
        self.assertEqual(mappings["tasks"][0]["apple_uid"], "apple-new")

    @patch("kriya.task_sync.get_reminders_for_sync")
    @patch("kriya.task_sync.get_tasks_for_sync", return_value=[])
    def test_run_task_sync_queues_google_create(self, _google, mock_apple):
        mock_apple.return_value = [
            {
                "uid": "a1",
                "title": "Buy milk",
                "due": "2026-05-06",
                "notes": "Whole",
                "completed": False,
                "updated": "2026-05-05T10:00:00Z",
            }
        ]
        with tempfile.TemporaryDirectory() as state_dir:
            result = run_task_sync(state_dir=state_dir)
            with open(result["queued_google"][0], encoding="utf-8") as f:
                pending = json.load(f)

        self.assertEqual(pending["tool"], "tasks.insert")
        self.assertEqual(pending["args"]["title"], "Buy milk")
        self.assertEqual(result["apple_results"], [])

    @patch("kriya.task_sync.get_reminders_for_sync")
    @patch("kriya.task_sync.get_tasks_for_sync", return_value=[])
    def test_run_task_sync_circuit_breaker_writes_review_item(self, _google, mock_apple):
        mock_apple.return_value = [
            {
                "uid": f"a{i}",
                "title": f"Task {i}",
                "completed": False,
                "updated": "2026-05-05T10:00:00Z",
            }
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as state_dir:
            result = run_task_sync(state_dir=state_dir, action_limit=2)
            plan_exists = os.path.exists(result["pending_plan"])
            with open(result["pending_review"], encoding="utf-8") as f:
                pending = json.load(f)

        self.assertTrue(result["aborted"])
        self.assertTrue(plan_exists)
        self.assertEqual(pending["tool"], "sync.review")
        self.assertEqual(pending["args"]["action_count"], 3)

    def test_format_task_sync_result(self):
        content = format_task_sync_result(
            {
                "aborted": False,
                "action_count": 2,
                "apple_results": [{"type": "create_apple"}],
                "queued_google": ["state/pending/x.json"],
                "mappings": "state/sync/mappings.json",
            }
        )

        self.assertIn("Task sync complete: 2 planned actions", content)
        self.assertIn("- apple writes: 1", content)
        self.assertIn("- queued google writes: 1", content)
