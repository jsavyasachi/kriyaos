import sys
import types
import unittest
from unittest.mock import patch


class FakeFastMCP:
    def __init__(self, _name):
        pass

    def tool(self):
        def decorator(func):
            return func

        return decorator


fake_mcp = types.ModuleType("mcp")
fake_mcp_server = types.ModuleType("mcp.server")
fake_fastmcp = types.ModuleType("mcp.server.fastmcp")
fake_fastmcp.FastMCP = FakeFastMCP
sys.modules.setdefault("mcp", fake_mcp)
sys.modules.setdefault("mcp.server", fake_mcp_server)
sys.modules.setdefault("mcp.server.fastmcp", fake_fastmcp)

from kriya import server  # noqa: E402


class TestServerTools(unittest.TestCase):
    @patch("kriya.server.build_brief_for_today", return_value="brief")
    def test_daily_brief_tool(self, mock_brief):
        self.assertEqual(server.daily_brief(), "brief")
        mock_brief.assert_called_once_with()

    @patch("kriya.server.append_email_triage", return_value="state/inbox.md")
    def test_email_triage_tool(self, mock_triage):
        self.assertEqual(server.email_triage(), "state/inbox.md")
        mock_triage.assert_called_once_with()

    @patch("kriya.server.write_tasks_snapshot", return_value="state/tasks.md")
    def test_tasks_tool(self, mock_tasks):
        self.assertEqual(server.tasks(), "state/tasks.md")
        mock_tasks.assert_called_once_with()

    @patch("kriya.server.write_notes_snapshot", return_value="state/notes.md")
    def test_notes_tool(self, mock_notes):
        self.assertEqual(server.notes(), "state/notes.md")
        mock_notes.assert_called_once_with()

    @patch("kriya.server.write_finance_snapshot", return_value="state/finance.md")
    def test_finance_tool(self, mock_finance):
        self.assertEqual(server.finance(display="INR", inr_per_usd=83.2), "state/finance.md")
        mock_finance.assert_called_once_with(display="INR", inr_per_usd=83.2)

    @patch("kriya.server.write_vitals_snapshot", return_value="state/vitals.md")
    def test_vitals_tool(self, mock_vitals):
        self.assertEqual(server.vitals(), "state/vitals.md")
        mock_vitals.assert_called_once_with()

    @patch("kriya.server.list_pending_actions", return_value=[])
    def test_approvals_tool(self, mock_list):
        self.assertEqual(server.approvals(), "No pending actions.\n")
        mock_list.assert_called_once_with()

    @patch(
        "kriya.server.run_poll",
        return_value={
            "date": "2026-04-30",
            "tasks": "t",
            "notes": "n",
            "groceries": "g",
            "finance": "f",
            "vitals": "v",
            "email_triage": "e",
            "daily_brief": "d",
        },
    )
    def test_poll_tool(self, mock_poll):
        self.assertIn("Poll complete: 2026-04-30", server.poll())
        mock_poll.assert_called_once_with()

    @patch("kriya.server.render_inbox", return_value="# Kriya Inbox\n")
    def test_inbox_tool(self, mock_inbox):
        self.assertEqual(server.inbox(), "# Kriya Inbox\n")
        mock_inbox.assert_called_once_with()

    @patch(
        "kriya.server.run_task_sync",
        return_value={
            "aborted": False,
            "action_count": 0,
            "apple_results": [],
            "queued_google": [],
            "mappings": "state/sync/mappings.json",
        },
    )
    def test_sync_tasks_tool(self, mock_sync):
        self.assertIn("Task sync complete: 0 planned actions", server.sync_tasks())
        mock_sync.assert_called_once_with()

    @patch("kriya.server.write_groceries_snapshot", return_value="state/groceries-2026-05-09.md")
    def test_groceries_tool(self, mock_write):
        self.assertEqual(server.groceries(), "state/groceries-2026-05-09.md")
        mock_write.assert_called_once_with()
