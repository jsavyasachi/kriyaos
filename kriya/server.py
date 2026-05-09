import datetime
import os
import sys

# Add the project root to sys.path to resolve kriya module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from kriya.approvals import approve_action, format_pending_actions, list_pending_actions, reject_action
from kriya.apple_reminders import get_reminders_by_list
from kriya.daily_brief import build_daily_brief, get_calendar_events, get_unread_emails
from kriya.email_triage import append_email_triage
from kriya.finance import get_networth_report, write_finance_snapshot
from kriya.google_keep import write_notes_snapshot
from kriya.google_tasks import format_tasks, get_open_tasks, write_tasks_snapshot
from kriya.grocery_sync import format_grocery_sync_result, run_grocery_sync
from kriya.memory import add as memory_add
from kriya.memory import search as memory_search
from kriya.inbox import render_inbox
from kriya.poll import format_poll_result, run_poll
from kriya.task_sync import format_task_sync_result, run_task_sync
from kriya.vitals import format_vitals_section, get_vitals_summary, write_vitals_snapshot

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
    finance_md = get_networth_report()
    vitals_md = format_vitals_section(get_vitals_summary())
    return build_daily_brief(
        today,
        events,
        emails,
        tasks_md=tasks_md,
        finance_md=finance_md,
        vitals_md=vitals_md,
    )


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
def notes() -> str:
    """
    Writes a read-only Google Keep notes snapshot to state/notes-YYYY-MM-DD.md.
    """
    return write_notes_snapshot()


@mcp.tool()
def finance(display: str = "USD", inr_per_usd: float | None = None) -> str:
    """
    Writes an f5e net-worth snapshot to state/finance-YYYY-MM-DD.md.
    """
    return write_finance_snapshot(display=display, inr_per_usd=inr_per_usd)


@mcp.tool()
def vitals() -> str:
    """
    Writes an Apple Health vitals snapshot to state/vitals-YYYY-MM-DD.md.
    """
    return write_vitals_snapshot()


@mcp.tool()
def approvals() -> str:
    """
    Lists pending approval-gated actions.
    """
    return format_pending_actions(list_pending_actions())


@mcp.tool()
def approve(approval_id: str) -> str:
    """
    Approves a pending action without executing it.
    """
    item = approve_action(approval_id)
    return f"Approved: {item['tool']} ({item['id']})"


@mcp.tool()
def execute(approval_id: str) -> str:
    """
    Executes an approved action through the deterministic executor.
    """
    from kriya.execute import execute_action

    item = execute_action(approval_id)
    return f"Executed: {item['tool']} ({item['id']})"


@mcp.tool()
def reject(approval_id: str) -> str:
    """
    Rejects a pending or approved action.
    """
    reject_action(approval_id)
    return f"Rejected: {approval_id}"


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
def sync_tasks() -> str:
    """
    Syncs Google Tasks and Apple Reminders, queueing Google writes for approval.
    """
    return format_task_sync_result(run_task_sync())


@mcp.tool()
def sync_groceries() -> str:
    """
    Syncs Google Keep Groceries and Apple Reminders Groceries, queueing Google writes for approval.
    """
    return format_grocery_sync_result(run_grocery_sync())


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
