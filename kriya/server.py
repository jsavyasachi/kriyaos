import datetime
import os
import sys

# Add the project root to sys.path to resolve kriya module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from kriya.approvals import format_pending_actions, list_pending_actions
from kriya.daily_brief import build_daily_brief, get_calendar_events, get_unread_emails
from kriya.email_triage import append_email_triage
from kriya.google_tasks import write_tasks_snapshot

# Create an MCP server
mcp = FastMCP("KriyaOS")


def build_brief_for_today() -> str:
    today = datetime.date.today().isoformat()
    events = get_calendar_events()
    emails = get_unread_emails()
    return build_daily_brief(today, events, emails)


@mcp.tool()
def daily_brief() -> str:
    """
    Generates a daily brief summary.
    """
    return build_brief_for_today()


@mcp.tool()
def email_triage() -> str:
    """
    Appends a read-only triage of unread emails to state/inbox.md.
    """
    return append_email_triage()


@mcp.tool()
def tasks() -> str:
    """
    Writes a read-only Google Tasks snapshot to state/tasks-YYYY-MM-DD.md.
    """
    return write_tasks_snapshot()


@mcp.tool()
def approvals() -> str:
    """
    Lists pending approval-gated actions.
    """
    return format_pending_actions(list_pending_actions())


@mcp.tool()
def get_daily_brief() -> str:
    """
    Deprecated alias for daily_brief.
    """
    return daily_brief()


@mcp.tool()
def triage_email() -> str:
    """
    Deprecated alias for email_triage.
    """
    return email_triage()


@mcp.tool()
def get_tasks() -> str:
    """
    Deprecated alias for tasks.
    """
    return tasks()

if __name__ == "__main__":
    mcp.run()
