import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from kriya.email_triage import (
    append_email_triage,
    classify_email,
    create_event_proposals,
    create_task_proposals,
    extract_event_times,
    format_triage,
    is_actionable_email,
    is_meeting_request,
    triage_emails,
)


class TestEmailTriage(unittest.TestCase):
    def test_classify_email(self):
        self.assertEqual(
            classify_email({"subject": "Security alert", "from": "Google", "snippet": ""}),
            "urgent",
        )
        self.assertEqual(
            classify_email({"subject": "Weekly digest", "from": "News", "snippet": ""}),
            "newsletter",
        )
        self.assertEqual(
            classify_email({"subject": "Order confirmation", "from": "no-reply@example.com", "snippet": ""}),
            "automated",
        )
        self.assertEqual(
            classify_email({"subject": "Lunch", "from": "Person", "snippet": "tomorrow?"}),
            "normal",
        )

    def test_triage_emails_groups_by_category(self):
        triaged = triage_emails(
            [
                {"subject": "ASAP", "from": "A", "snippet": ""},
                {"subject": "Hello", "from": "B", "snippet": ""},
            ]
        )

        self.assertEqual(len(triaged["urgent"]), 1)
        self.assertEqual(len(triaged["normal"]), 1)

    def test_is_actionable_email(self):
        self.assertTrue(is_actionable_email({"subject": "Security alert", "snippet": ""}, "urgent"))
        self.assertTrue(is_actionable_email({"subject": "Hello", "snippet": "please review"}, "normal"))
        self.assertFalse(is_actionable_email({"subject": "Hello", "snippet": "FYI"}, "normal"))

    def test_create_task_proposals_writes_pending_actions(self):
        with tempfile.TemporaryDirectory() as state_dir:
            paths = create_task_proposals(
                {
                    "urgent": [{"from": "A", "subject": "Security alert", "snippet": "Verify login"}],
                    "normal": [],
                    "newsletter": [],
                    "automated": [],
                },
                state_dir,
            )

            with open(paths[0], encoding="utf-8") as f:
                item = json.load(f)

        self.assertEqual(len(paths), 1)
        self.assertEqual(item["tool"], "tasks.insert")
        self.assertEqual(item["args"]["title"], "Follow up: Security alert")

    def test_is_meeting_request_detects_meeting_terms(self):
        self.assertTrue(is_meeting_request({"subject": "Quick sync?", "snippet": ""}))
        self.assertTrue(is_meeting_request({"subject": "Interview invitation", "snippet": ""}))
        self.assertTrue(is_meeting_request({"subject": "Hi", "snippet": "can we hop on a zoom call"}))
        self.assertFalse(is_meeting_request({"subject": "Invoice attached", "snippet": "Please pay"}))

    def test_extract_event_times_returns_iso_strings(self):
        start, end = extract_event_times({"subject": "meeting", "snippet": ""})
        self.assertRegex(start, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        self.assertRegex(end, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_extract_event_times_end_is_one_hour_after_start(self):
        import datetime
        start_str, end_str = extract_event_times({"subject": "meet", "snippet": ""})
        start = datetime.datetime.fromisoformat(start_str)
        end = datetime.datetime.fromisoformat(end_str)
        self.assertEqual(end - start, datetime.timedelta(hours=1))

    def test_create_event_proposals_detects_meeting_emails(self):
        with tempfile.TemporaryDirectory() as state_dir:
            paths = create_event_proposals(
                {
                    "urgent": [],
                    "normal": [{"from": "Alice <alice@co.com>", "subject": "Quick sync?", "snippet": "can we meet tomorrow?"}],
                    "newsletter": [],
                    "automated": [],
                },
                state_dir,
            )
            self.assertEqual(len(paths), 1)
            with open(paths[0], encoding="utf-8") as f:
                item = json.load(f)

        self.assertEqual(item["tool"], "calendar.create_event")
        self.assertEqual(item["args"]["summary"], "Quick sync?")
        self.assertIn("start", item["args"])
        self.assertIn("end", item["args"])

    def test_create_event_proposals_skips_non_meeting_emails(self):
        with tempfile.TemporaryDirectory() as state_dir:
            paths = create_event_proposals(
                {
                    "urgent": [{"from": "A", "subject": "Invoice overdue", "snippet": "Pay now"}],
                    "normal": [],
                    "newsletter": [],
                    "automated": [],
                },
                state_dir,
            )
        self.assertEqual(len(paths), 0)

    def test_format_triage_counts_sections(self):
        content = format_triage(
            "2026-04-30",
            {
                "urgent": [{"from": "A", "subject": "Security alert", "snippet": "Check login"}],
                "normal": [],
                "newsletter": [],
                "automated": [],
            },
        )

        self.assertIn("## Email Triage: 2026-04-30", content)
        self.assertIn("### Urgent (1)", content)
        self.assertIn("- **A**: Security alert", content)
        self.assertIn("### Normal (0)", content)

    @patch("kriya.email_triage.get_unread_emails")
    def test_append_email_triage_writes_inbox(self, mock_get_unread):
        mock_get_unread.return_value = [{"from": "A", "subject": "Hello", "snippet": "World"}]

        with tempfile.TemporaryDirectory() as state_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                inbox_path = append_email_triage(
                    state_dir=state_dir,
                    today="2026-04-30",
                    max_results=1,
                )

            with open(inbox_path, encoding="utf-8") as f:
                contents = f.read()

        self.assertTrue(inbox_path.endswith("inbox.md"))
        self.assertIn("## Email Triage: 2026-04-30", contents)
        self.assertIn("- **A**: Hello", contents)
        mock_get_unread.assert_called_once_with(max_results=1)

    @patch("kriya.email_triage.get_unread_emails")
    def test_append_email_triage_skips_existing_run(self, mock_get_unread):
        with tempfile.TemporaryDirectory() as state_dir:
            runs_dir = os.path.join(state_dir, "runs")
            os.makedirs(runs_dir)
            with open(os.path.join(runs_dir, "2026-04-30-email_triage.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "completed"}, f)

            with contextlib.redirect_stdout(io.StringIO()):
                inbox_path = append_email_triage(state_dir=state_dir, today="2026-04-30")

        self.assertTrue(inbox_path.endswith("inbox.md"))
        mock_get_unread.assert_not_called()
