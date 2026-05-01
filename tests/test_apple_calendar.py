import json
import unittest
from unittest.mock import MagicMock, patch


class TestAppleCalendar(unittest.TestCase):
    def _raw_event(self, title="Standup", start="2026-04-30T09:00:00Z", all_day=False):
        return {"title": title, "start_date": start, "all_day": all_day, "calendar": "Work"}

    @patch("subprocess.run")
    def test_returns_normalized_events(self, mock_run):
        mock_run.return_value = MagicMock(stdout=json.dumps([self._raw_event()]))
        from kriya.apple_calendar import get_events
        events = get_events(days=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Standup")
        self.assertEqual(events[0]["start"], "2026-04-30T09:00:00Z")
        self.assertFalse(events[0]["all_day"])

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_returns_none_when_not_installed(self, _):
        from kriya.apple_calendar import get_events
        self.assertIsNone(get_events())

    @patch("subprocess.run")
    def test_uses_upcoming_for_multi_day(self, mock_run):
        mock_run.return_value = MagicMock(stdout=json.dumps([]))
        from kriya.apple_calendar import get_events
        get_events(days=7)
        cmd = mock_run.call_args[0][0]
        self.assertIn("upcoming", cmd)
        self.assertIn("-d", cmd)
        self.assertIn("7", cmd)

    @patch("subprocess.run")
    def test_uses_today_for_single_day(self, mock_run):
        mock_run.return_value = MagicMock(stdout=json.dumps([]))
        from kriya.apple_calendar import get_events
        get_events(days=1)
        cmd = mock_run.call_args[0][0]
        self.assertIn("today", cmd)
