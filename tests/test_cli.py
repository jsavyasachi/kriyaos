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
