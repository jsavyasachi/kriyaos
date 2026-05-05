import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from kriya.finance import format_finance_section, get_networth_report, write_finance_snapshot


class TestFinance(unittest.TestCase):
    @patch("kriya.finance.log_tool_call")
    @patch("kriya.finance.subprocess.run")
    def test_get_networth_report_shells_into_f5e(self, mock_run, _audit):
        mock_run.return_value = Mock(stdout="Net worth: $123\n")

        report = get_networth_report(display="USD", inr_per_usd=83.2, state_dir="tmp-state")

        self.assertEqual(report, "Net worth: $123")
        mock_run.assert_called_once_with(
            [
                "uv",
                "run",
                "python",
                "-m",
                "f5e.analyze.networth",
                "--display",
                "USD",
                "--inr-per-usd",
                "83.2",
            ],
            cwd="/Users/savya/projects/f5e",
            capture_output=True,
            text=True,
            check=True,
        )

    @patch.dict("os.environ", {"KRIYA_F5E_REPO": "/tmp/f5e"})
    @patch("kriya.finance.log_tool_call")
    @patch("kriya.finance.subprocess.run")
    def test_get_networth_report_uses_env_repo(self, mock_run, _audit):
        mock_run.return_value = Mock(stdout="Net worth: $123\n")

        get_networth_report(state_dir="tmp-state")

        self.assertEqual(mock_run.call_args.kwargs["cwd"], "/tmp/f5e")

    @patch("kriya.finance.log_error")
    @patch("kriya.finance.log_tool_call")
    @patch("kriya.finance.subprocess.run")
    def test_get_networth_report_returns_empty_on_failure(self, mock_run, _audit, mock_error):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["uv"], stderr="boom")

        self.assertEqual(get_networth_report(state_dir="tmp-state"), "")
        mock_error.assert_called_once()

    @patch("kriya.finance.get_networth_report", return_value="Net worth: $123")
    def test_write_finance_snapshot(self, mock_report):
        with tempfile.TemporaryDirectory() as state_dir:
            path = write_finance_snapshot(state_dir=state_dir, today="2026-05-05")

            with open(path, encoding="utf-8") as f:
                contents = f.read()

        self.assertTrue(path.endswith("finance-2026-05-05.md"))
        self.assertIn("# Finance 2026-05-05", contents)
        self.assertIn("Net worth: $123", contents)
        mock_report.assert_called_once_with(display="USD", inr_per_usd=None, state_dir=state_dir)

    @patch("kriya.finance.get_networth_report", return_value="")
    def test_write_finance_snapshot_records_unavailable(self, _mock_report):
        with tempfile.TemporaryDirectory() as state_dir:
            path = write_finance_snapshot(state_dir=state_dir, today="2026-05-05")

            with open(path, encoding="utf-8") as f:
                contents = f.read()

        self.assertIn("_unavailable_", contents)
        self.assertEqual(format_finance_section(""), "Finance unavailable.\n")
