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

    @patch("kriya.cli.write_notes_snapshot")
    def test_notes_command(self, mock_notes):
        result = main(
            [
                "notes",
                "--state-dir",
                "tmp-state",
                "--date",
                "2026-05-05",
                "--page-size",
                "3",
            ]
        )

        self.assertEqual(result, 0)
        mock_notes.assert_called_once_with(
            state_dir="tmp-state",
            today="2026-05-05",
            page_size=3,
        )

    @patch("kriya.cli.write_finance_snapshot")
    def test_finance_command(self, mock_finance):
        result = main(
            [
                "finance",
                "--state-dir",
                "tmp-state",
                "--date",
                "2026-05-05",
                "--display",
                "INR",
                "--inr-per-usd",
                "83.2",
            ]
        )

        self.assertEqual(result, 0)
        mock_finance.assert_called_once_with(
            state_dir="tmp-state",
            today="2026-05-05",
            display="INR",
            inr_per_usd=83.2,
        )

    @patch("kriya.cli.write_vitals_snapshot")
    def test_vitals_command(self, mock_vitals):
        result = main(["vitals", "--state-dir", "tmp-state", "--date", "2026-05-05"])

        self.assertEqual(result, 0)
        mock_vitals.assert_called_once_with(state_dir="tmp-state", today="2026-05-05")

    @patch("kriya.cli.list_pending_actions", return_value=[])
    def test_approvals_command(self, mock_list):
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["approvals", "--state-dir", "tmp-state"])

        self.assertEqual(result, 0)
        mock_list.assert_called_once_with("tmp-state")

    @patch(
        "kriya.cli.run_poll",
        return_value={
            "date": "2026-04-30",
            "tasks": "t",
            "notes": "n",
            "finance": "f",
            "vitals": "v",
            "email_triage": "e",
            "daily_brief": "d",
        },
    )
    def test_poll_command(self, mock_poll):
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["poll", "--state-dir", "tmp-state", "--date", "2026-04-30", "--force"])

        self.assertEqual(result, 0)
        mock_poll.assert_called_once_with(state_dir="tmp-state", today="2026-04-30", force=True)

    @patch("kriya.cli.render_inbox", return_value="# Kriya Inbox\n")
    def test_inbox_command(self, mock_inbox):
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["inbox", "--state-dir", "tmp-state"])

        self.assertEqual(result, 0)
        mock_inbox.assert_called_once_with("tmp-state")

    @patch(
        "kriya.cli.run_task_sync",
        return_value={
            "aborted": False,
            "action_count": 0,
            "apple_results": [],
            "queued_google": [],
            "mappings": "state/sync/mappings.json",
        },
    )
    def test_sync_tasks_command(self, mock_sync):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result = main(["sync-tasks", "--state-dir", "tmp-state", "--action-limit", "2"])

        self.assertEqual(result, 0)
        mock_sync.assert_called_once_with(state_dir="tmp-state", action_limit=2)
        self.assertIn("Task sync complete: 0 planned actions", stdout.getvalue())

    @patch("kriya.cli.write_groceries_snapshot", return_value="tmp-state/groceries-2026-05-09.md")
    def test_groceries_command(self, mock_write):
        with contextlib.redirect_stdout(io.StringIO()):
            result = main(["groceries", "--state-dir", "tmp-state", "--date", "2026-05-09"])

        self.assertEqual(result, 0)
        mock_write.assert_called_once_with(state_dir="tmp-state", today="2026-05-09")

    @patch("kriya.cli.approve_action", return_value={"id": "abc", "tool": "tasks.insert"})
    def test_approve_command_only_approves(self, mock_approve):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result = main(["approve", "abc", "--state-dir", "tmp-state"])

        self.assertEqual(result, 0)
        mock_approve.assert_called_once_with("abc", "tmp-state")
        self.assertEqual(stdout.getvalue(), "Approved: tasks.insert (abc)\n")

    @patch("kriya.execute.execute_action", return_value={"id": "abc", "tool": "tasks.insert"})
    def test_execute_command_executes_approved_action(self, mock_execute):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result = main(["execute", "abc", "--state-dir", "tmp-state"])

        self.assertEqual(result, 0)
        mock_execute.assert_called_once_with("abc", "tmp-state")
        self.assertEqual(stdout.getvalue(), "Executed: tasks.insert (abc)\n")

    @patch("kriya.cli.reject_action")
    def test_reject_command(self, mock_reject):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            result = main(["reject", "abc", "--state-dir", "tmp-state"])

        self.assertEqual(result, 0)
        mock_reject.assert_called_once_with("abc", "tmp-state")
        self.assertEqual(stdout.getvalue(), "Rejected: abc\n")
