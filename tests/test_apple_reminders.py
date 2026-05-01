import json
import unittest
from unittest.mock import MagicMock, patch


class TestAppleReminders(unittest.TestCase):
    def _raw_reminder(self, name="Buy milk", list_name="Personal", due_date=None, body=""):
        return {
            "id": "abc123",
            "name": name,
            "body": body,
            "list_name": list_name,
            "due_date": due_date,
            "completed": False,
        }

    @patch("subprocess.run")
    def test_groups_by_list(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps([
                self._raw_reminder("Buy milk", "Personal"),
                self._raw_reminder("Call dentist", "Personal"),
                self._raw_reminder("Code review", "Work"),
            ])
        )
        from kriya.apple_reminders import get_reminders_by_list
        groups = get_reminders_by_list()
        titles = {g["list"]["title"] for g in groups}
        self.assertIn("Personal (Reminders)", titles)
        self.assertIn("Work (Reminders)", titles)
        personal = next(g for g in groups if "Personal" in g["list"]["title"])
        self.assertEqual(len(personal["tasks"]), 2)

    @patch("subprocess.run")
    def test_truncates_due_date_to_date(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps([self._raw_reminder(due_date="2026-04-30T09:00:00")])
        )
        from kriya.apple_reminders import get_reminders_by_list
        groups = get_reminders_by_list()
        task = groups[0]["tasks"][0]
        self.assertEqual(task["due"], "2026-04-30")

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_none_when_not_installed(self, _):
        from kriya.apple_reminders import get_reminders_by_list
        self.assertIsNone(get_reminders_by_list())

    @patch("subprocess.run")
    def test_passes_incomplete_flag(self, mock_run):
        mock_run.return_value = MagicMock(stdout=json.dumps([]))
        from kriya.apple_reminders import get_reminders_by_list
        get_reminders_by_list()
        cmd = mock_run.call_args[0][0]
        self.assertIn("--incomplete", cmd)
