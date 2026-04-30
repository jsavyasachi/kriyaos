import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from kriya.google_tasks import format_tasks, write_tasks_snapshot


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
