import json
import os
import contextlib
import io
import tempfile
import unittest
from unittest.mock import patch

from kriya.daily_brief import build_daily_brief, generate_daily_brief


class TestDailyBrief(unittest.TestCase):
    def test_build_daily_brief_formats_sections(self):
        brief = build_daily_brief(
            "2026-04-30",
            [{"title": "Standup", "start": "2026-04-30T09:15:00-04:00", "all_day": False}],
            [{"from": "A <a@example.com>", "subject": "Hello", "snippet": "World"}],
        )

        self.assertIn("# Daily Brief: 2026-04-30", brief)
        self.assertIn("- **2026-04-30 09:15**: Standup", brief)
        self.assertIn("- **A <a@example.com>**: Hello", brief)
        self.assertIn("Finance summary placeholder", brief)
        self.assertIn("No recent errors logged.", brief)

    def test_build_daily_brief_formats_errors(self):
        brief = build_daily_brief(
            "2026-04-30",
            [],
            [],
            [{"timestamp": "2026-04-30T01:00:00Z", "source": "daily_brief.email", "message": "boom"}],
        )

        self.assertIn("## ⚠️ Errors", brief)
        self.assertIn("`daily_brief.email`: boom", brief)

    def test_build_daily_brief_formats_tasks(self):
        brief = build_daily_brief("2026-04-30", [], [], tasks_md="### To Do (1)\n- **Ship**\n")

        self.assertIn("## ✅ Tasks", brief)
        self.assertIn("- **Ship**", brief)

    @patch("kriya.daily_brief.get_unread_emails", return_value=[])
    @patch("kriya.daily_brief.get_calendar_events", return_value=[])
    def test_generate_daily_brief_writes_run_marker(self, _calendar, _emails):
        with tempfile.TemporaryDirectory() as state_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                brief_path = generate_daily_brief(state_dir=state_dir, today="2026-04-30")
            run_path = os.path.join(state_dir, "runs", "2026-04-30-daily_brief.json")

            self.assertTrue(os.path.exists(brief_path))
            self.assertTrue(os.path.exists(run_path))
            with open(run_path, encoding="utf-8") as f:
                marker = json.load(f)

        self.assertEqual(marker["skill"], "daily_brief")
        self.assertEqual(marker["status"], "completed")

    @patch("kriya.daily_brief.get_unread_emails")
    @patch("kriya.daily_brief.get_calendar_events")
    def test_generate_daily_brief_skips_existing_run(self, mock_calendar, mock_emails):
        with tempfile.TemporaryDirectory() as state_dir:
            runs_dir = os.path.join(state_dir, "runs")
            os.makedirs(runs_dir)
            with open(os.path.join(runs_dir, "2026-04-30-daily_brief.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "completed"}, f)

            with contextlib.redirect_stdout(io.StringIO()):
                brief_path = generate_daily_brief(state_dir=state_dir, today="2026-04-30")

        self.assertTrue(brief_path.endswith("daily-brief-2026-04-30.md"))
        mock_calendar.assert_not_called()
        mock_emails.assert_not_called()

    @patch("kriya.daily_brief.get_unread_emails")
    @patch("kriya.daily_brief.get_calendar_events")
    def test_generate_daily_brief_skips_when_cost_ceiling_reached(self, mock_calendar, mock_emails):
        with tempfile.TemporaryDirectory() as state_dir:
            with open(os.path.join(state_dir, "usage.jsonl"), "w", encoding="utf-8") as f:
                f.write('{"timestamp":"2026-04-30T01:00:00Z","cost_usd":2.0}\n')

            with contextlib.redirect_stdout(io.StringIO()):
                brief_path = generate_daily_brief(state_dir=state_dir, today="2026-04-30")

        self.assertTrue(brief_path.endswith("daily-brief-2026-04-30.md"))
        mock_calendar.assert_not_called()
        mock_emails.assert_not_called()
