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

    def test_normalize_reminder_for_sync(self):
        from kriya.apple_reminders import normalize_reminder_for_sync

        task = normalize_reminder_for_sync(
            self._raw_reminder(
                name="Buy milk",
                list_name="Personal",
                due_date="2026-04-30T09:00:00",
                body="Whole",
            )
        )

        self.assertEqual(task["uid"], "abc123")
        self.assertEqual(task["list_name"], "Personal")
        self.assertEqual(task["due"], "2026-04-30")
        self.assertEqual(task["notes"], "Whole")

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

    @patch("subprocess.run")
    def test_add_reminder_uses_osascript(self, mock_run):
        mock_run.return_value = MagicMock(stdout="uid123\n")
        from kriya.apple_reminders import add_reminder

        uid = add_reminder("Personal", "Buy milk", due="2026-05-05", notes="Whole")

        self.assertEqual(uid, "uid123")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[:2], ["osascript", "-e"])
        self.assertIn('make new reminder', cmd[2])
        self.assertIn('list "Personal"', cmd[2])
        self.assertIn('name:"Buy milk"', cmd[2])

    @patch("subprocess.run")
    def test_update_reminder_uses_osascript(self, mock_run):
        mock_run.return_value = MagicMock(stdout="uid123\n")
        from kriya.apple_reminders import update_reminder

        uid = update_reminder("uid123", title="Buy coffee", notes="Beans")

        self.assertEqual(uid, "uid123")
        script = mock_run.call_args[0][0][2]
        self.assertIn('whose id is "uid123"', script)
        self.assertIn('set name of targetReminder to "Buy coffee"', script)
        self.assertIn('set body of targetReminder to "Beans"', script)

    @patch("subprocess.run")
    def test_complete_reminder_uses_osascript(self, mock_run):
        mock_run.return_value = MagicMock(stdout="uid123\n")
        from kriya.apple_reminders import complete_reminder

        uid = complete_reminder("uid123")

        self.assertEqual(uid, "uid123")
        self.assertIn("set completed of targetReminder to true", mock_run.call_args[0][0][2])

    @patch("subprocess.run")
    def test_delete_reminder_uses_osascript(self, mock_run):
        mock_run.return_value = MagicMock(stdout="uid123\n")
        from kriya.apple_reminders import delete_reminder

        uid = delete_reminder("uid123")

        self.assertEqual(uid, "uid123")
        self.assertIn('delete first reminder whose id is "uid123"', mock_run.call_args[0][0][2])
