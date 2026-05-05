import unittest
from unittest.mock import patch

from kriya.poll import format_poll_result, run_poll


class TestPoll(unittest.TestCase):
    @patch("kriya.poll.generate_daily_brief", return_value="state/daily.md")
    @patch("kriya.poll.append_email_triage", return_value="state/inbox.md")
    @patch("kriya.poll.write_vitals_snapshot", return_value="state/vitals.md")
    @patch("kriya.poll.write_finance_snapshot", return_value="state/finance.md")
    @patch("kriya.poll.write_tasks_snapshot", return_value="state/tasks.md")
    def test_run_poll(self, mock_tasks, mock_finance, mock_vitals, mock_triage, mock_brief):
        result = run_poll(state_dir="tmp-state", today="2026-04-30", force=True)

        self.assertEqual(result["date"], "2026-04-30")
        self.assertEqual(result["tasks"], "state/tasks.md")
        self.assertEqual(result["finance"], "state/finance.md")
        self.assertEqual(result["vitals"], "state/vitals.md")
        mock_tasks.assert_called_once_with(state_dir="tmp-state", today="2026-04-30")
        mock_finance.assert_called_once_with(state_dir="tmp-state", today="2026-04-30")
        mock_vitals.assert_called_once_with(state_dir="tmp-state", today="2026-04-30")
        mock_triage.assert_called_once_with(state_dir="tmp-state", today="2026-04-30", force=True)
        mock_brief.assert_called_once_with(state_dir="tmp-state", today="2026-04-30", force=True)

    def test_format_poll_result(self):
        content = format_poll_result(
            {
                "date": "2026-04-30",
                "tasks": "state/tasks.md",
                "finance": "state/finance.md",
                "vitals": "state/vitals.md",
                "email_triage": "state/inbox.md",
                "daily_brief": "state/daily.md",
            }
        )

        self.assertIn("Poll complete: 2026-04-30", content)
        self.assertIn("- tasks: state/tasks.md", content)
        self.assertIn("- finance: state/finance.md", content)
        self.assertIn("- vitals: state/vitals.md", content)
