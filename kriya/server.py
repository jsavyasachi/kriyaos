import datetime
import os
import sys

# Add the project root to sys.path to resolve kriya module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from kriya.approvals import format_pending_actions, list_pending_actions
from kriya.apple_reminders import get_reminders_by_list
from kriya.daily_brief import build_daily_brief, get_calendar_events, get_unread_emails
from kriya.email_triage import append_email_triage
from kriya.google_tasks import format_tasks, get_open_tasks, write_tasks_snapshot
from kriya.memory import add as memory_add
from kriya.memory import get_all as memory_get_all
from kriya.memory import search as memory_search
from kriya.inbox import render_inbox
from kriya.poll import format_poll_result, run_poll

# Create an MCP server
mcp = FastMCP("KriyaOS")


def build_brief_for_today() -> str:
    today = datetime.date.today().isoformat()
    events = get_calendar_events()
    emails = get_unread_emails()
    tasks_by_list = get_open_tasks()
    reminders = get_reminders_by_list()
    if reminders:
        tasks_by_list = tasks_by_list + reminders
    tasks_md = format_tasks(tasks_by_list, today)
    return build_daily_brief(today, events, emails, tasks_md=tasks_md)


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
def poll() -> str:
    """
    Runs a bounded read-only polling cycle.
    """
    return format_poll_result(run_poll())


@mcp.tool()
def inbox() -> str:
    """
    Renders current local Kriya OS state.
    """
    return render_inbox()


@mcp.tool()
def remember(text: str) -> str:
    """
    Stores a memory about the user: preferences, context, facts, recurring patterns.
    """
    ok = memory_add(text)
    return "Remembered." if ok else "Memory store unavailable."


@mcp.tool()
def recall(query: str) -> str:
    """
    Searches stored memories relevant to a query.
    """
    results = memory_search(query, limit=5)
    if not results:
        return "No relevant memories found."
    return "\n".join(f"- {m}" for m in results)


if __name__ == "__main__":
    mcp.run()
