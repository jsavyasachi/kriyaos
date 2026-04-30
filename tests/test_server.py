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

from kriya import server


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

    @patch("kriya.server.list_pending_actions", return_value=[])
    def test_approvals_tool(self, mock_list):
        self.assertEqual(server.approvals(), "No pending actions.\n")
        mock_list.assert_called_once_with()

    @patch("kriya.server.daily_brief", return_value="brief")
    def test_old_daily_brief_alias(self, mock_daily_brief):
        self.assertEqual(server.get_daily_brief(), "brief")
        mock_daily_brief.assert_called_once_with()

    @patch("kriya.server.email_triage", return_value="state/inbox.md")
    def test_old_email_triage_alias(self, mock_email_triage):
        self.assertEqual(server.triage_email(), "state/inbox.md")
        mock_email_triage.assert_called_once_with()

    @patch("kriya.server.tasks", return_value="state/tasks.md")
    def test_old_tasks_alias(self, mock_tasks):
        self.assertEqual(server.get_tasks(), "state/tasks.md")
        mock_tasks.assert_called_once_with()
