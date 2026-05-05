import contextlib
import io
import tempfile
import unittest
from unittest.mock import patch

from kriya.google_tasks import (
    complete_task,
    delete_task,
    format_tasks,
    normalize_task_for_sync,
    update_task,
    write_tasks_snapshot,
)


class TestGoogleTasks(unittest.TestCase):
    def test_format_tasks_handles_empty(self):
        self.assertEqual(format_tasks([], "2026-04-30"), "No open tasks found.\n")

    def test_format_tasks_groups_by_list(self):
        content = format_tasks(
            [
                {
                    "list": {"title": "To Do"},
                    "tasks": [
                        {
                            "title": "File taxes",
                            "due": "2026-04-30T00:00:00.000Z",
                            "notes": "Use official report",
                        }
                    ],
                }
            ],
            "2026-04-30",
        )

        self.assertIn("### To Do (1)", content)
        self.assertIn("- **File taxes** due today", content)
        self.assertIn("  - Use official report", content)

    def test_normalize_task_for_sync(self):
        task = normalize_task_for_sync(
            {
                "id": "task123",
                "title": "File taxes",
                "due": "2026-05-05T00:00:00.000Z",
                "notes": "Use report",
                "status": "completed",
                "deleted": False,
                "updated": "2026-05-05T10:00:00Z",
            },
            "list123",
        )

        self.assertEqual(task["id"], "task123")
        self.assertEqual(task["tasklist"], "list123")
        self.assertEqual(task["due"], "2026-05-05")
        self.assertTrue(task["completed"])

    @patch("kriya.google_tasks.get_open_tasks")
    def test_write_tasks_snapshot(self, mock_get_open_tasks):
        mock_get_open_tasks.return_value = [{"list": {"title": "To Do"}, "tasks": []}]

        with tempfile.TemporaryDirectory() as state_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                path = write_tasks_snapshot(state_dir=state_dir, today="2026-04-30")

            with open(path, encoding="utf-8") as f:
                contents = f.read()

        self.assertTrue(path.endswith("tasks-2026-04-30.md"))
        self.assertIn("# Tasks: 2026-04-30", contents)
        mock_get_open_tasks.assert_called_once_with(max_lists=10, max_tasks_per_list=20)

    @patch("kriya.google_tasks.run_gws", side_effect=RuntimeError("gws CLI not found on PATH"))
    def test_get_task_lists_raises_when_gws_missing(self, _gws):
        from kriya.google_tasks import get_task_lists
        with self.assertRaises(RuntimeError):
            get_task_lists()

    @patch("kriya.google_tasks.run_gws", return_value={"id": "task123"})
    def test_update_task_uses_patch(self, mock_gws):
        update_task({"id": "task123", "tasklist": "@default", "title": "New", "notes": "N"})

        self.assertEqual(mock_gws.call_args[0][0], "tasks.tasks.patch")
        params = mock_gws.call_args[0][1]
        self.assertEqual(params["task"], "task123")
        self.assertEqual(params["title"], "New")
        self.assertEqual(params["notes"], "N")

    @patch("kriya.google_tasks.run_gws", return_value={"id": "task123", "status": "completed"})
    def test_complete_task_sets_completed_status(self, mock_gws):
        complete_task({"id": "task123", "completed": "2026-05-05T12:00:00Z"})

        params = mock_gws.call_args[0][1]
        self.assertEqual(mock_gws.call_args[0][0], "tasks.tasks.patch")
        self.assertEqual(params["status"], "completed")
        self.assertEqual(params["completed"], "2026-05-05T12:00:00Z")

    @patch("kriya.google_tasks.run_gws", return_value={})
    def test_delete_task_uses_delete(self, mock_gws):
        delete_task({"id": "task123", "tasklist": "@default"})

        self.assertEqual(mock_gws.call_args[0][0], "tasks.tasks.delete")
        self.assertEqual(mock_gws.call_args[0][1], {"tasklist": "@default", "task": "task123"})
