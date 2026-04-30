import contextlib
import io
import unittest
from unittest.mock import patch

from kriya.cli import main


class TestCli(unittest.TestCase):
    @patch("kriya.cli.generate_daily_brief")
    def test_daily_brief_command(self, mock_generate):
        result = main(["daily-brief", "--state-dir", "tmp-state", "--date", "2026-04-30", "--force"])

        self.assertEqual(result, 0)
        mock_generate.assert_called_once_with(
            state_dir="tmp-state",
            today="2026-04-30",
            force=True,
        )

    @patch("kriya.cli.append_email_triage")
    def test_email_triage_command(self, mock_triage):
        result = main(
            [
                "email-triage",
                "--state-dir",
                "tmp-state",
                "--date",
                "2026-04-30",
                "--max-results",
                "3",
                "--force",
            ]
        )

        self.assertEqual(result, 0)
        mock_triage.assert_called_once_with(
            state_dir="tmp-state",
            today="2026-04-30",
            max_results=3,
            force=True,
        )

    @patch("kriya.cli.write_tasks_snapshot")
    def test_tasks_command(self, mock_tasks):
        result = main(
            [
                "tasks",
                "--state-dir",
                "tmp-state",
                "--date",
                "2026-04-30",
                "--max-lists",
                "2",
                "--max-tasks-per-list",
                "4",
            ]
        )

        self.assertEqual(result, 0)
        mock_tasks.assert_called_once_with(
            state_dir="tmp-state",
            today="2026-04-30",
            max_lists=2,
            max_tasks_per_list=4,
        )

    @patch("kriya.cli.list_pending_actions", return_value=[])
    def test_approvals_command(self, mock_list):
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["approvals", "--state-dir", "tmp-state"])

        self.assertEqual(result, 0)
        mock_list.assert_called_once_with("tmp-state")
