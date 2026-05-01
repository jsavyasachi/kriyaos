import json
import subprocess

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error


def get_reminders_by_list():
    """Returns incomplete reminders grouped as tasks_by_list, or None if rem is not installed."""
    try:
        result = subprocess.run(
            ["rem", "list", "--incomplete", "-o", "json"],
            capture_output=True, text=True, check=True,
        )
        raw = json.loads(result.stdout)
        log_tool_call("rem.list", {"incomplete": True}, "ok", {"count": len(raw)})
        return _group_by_list(raw)
    except FileNotFoundError:
        return None
    except Exception as e:
        log_error("apple_reminders", str(e), {})
        return []


def _group_by_list(reminders):
    groups: dict[str, list] = {}
    for r in reminders:
        list_name = r.get("list_name", "Reminders")
        due_raw = r.get("due_date") or ""
        groups.setdefault(list_name, []).append({
            "title": r.get("name", "(No Title)"),
            "due": due_raw[:10] if due_raw else None,
            "notes": r.get("body", ""),
        })
    return [
        {"list": {"title": f"{name} (Reminders)", "id": None}, "tasks": tasks}
        for name, tasks in groups.items()
    ]
