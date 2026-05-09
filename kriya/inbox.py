import os

from kriya.approvals import format_pending_actions, list_pending_actions
from kriya.utils.errors import read_recent_errors


def latest_matching_file(state_dir, prefix, suffix=".md"):
    if not os.path.exists(state_dir):
        return None
    matches = [
        os.path.join(state_dir, name)
        for name in os.listdir(state_dir)
        if name.startswith(prefix) and name.endswith(suffix)
    ]
    if not matches:
        return None
    return sorted(matches)[-1]


def read_file_or_empty(path):
    if path is None or not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def format_recent_errors(errors):
    if not errors:
        return "No recent errors."
    lines = []
    for error in errors:
        timestamp = error.get("timestamp", "(unknown time)")
        source = error.get("source", "(unknown source)")
        message = error.get("message", "")
        lines.append(f"- **{timestamp}** `{source}`: {message}")
    return "\n".join(lines)


def render_inbox(state_dir="state"):
    latest_tasks = latest_matching_file(state_dir, "tasks-")
    latest_groceries = latest_matching_file(state_dir, "groceries-")
    latest_brief = latest_matching_file(state_dir, "daily-brief-")
    inbox_path = os.path.join(state_dir, "inbox.md")
    pending = format_pending_actions(list_pending_actions(state_dir)).strip()
    errors = format_recent_errors(read_recent_errors(state_dir)).strip()
    tasks = read_file_or_empty(latest_tasks) or "No tasks snapshot found."
    groceries = read_file_or_empty(latest_groceries) or "No groceries snapshot found."
    triage = read_file_or_empty(inbox_path) or "No email triage found."

    return f"""# Kriya Inbox

## Pending Approvals
{pending}

## Recent Errors
{errors}

## Latest Tasks
{tasks}

## Latest Groceries
{groceries}

## Email Triage
{triage}

## Latest Daily Brief
{latest_brief or "No daily brief found."}
"""


if __name__ == "__main__":
    print(render_inbox(), end="")
