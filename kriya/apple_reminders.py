import json
import subprocess
from typing import Any

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


def add_reminder(list_name: str, title: str, due: str | None = None, notes: str | None = None) -> str:
    args = {"list_name": list_name, "title": title, "due": due, "notes": notes}
    properties = [f"name:{_as_string(title)}"]
    if notes:
        properties.append(f"body:{_as_string(notes)}")
    script = [
        'tell application "Reminders"',
        f"set targetList to list {_as_string(list_name)}",
        f"set newReminder to make new reminder at end of reminders of targetList with properties {{{', '.join(properties)}}}",
    ]
    if due:
        script.append(f"set due date of newReminder to date {_as_string(due + ' 00:00:00')}")
    script.extend(["return id of newReminder", "end tell"])
    return _run_osascript("\n".join(script), "reminders.add", args)


def update_reminder(uid: str, title: str | None = None, due: str | None = None, notes: str | None = None) -> str:
    args = {"uid": uid, "title": title, "due": due, "notes": notes}
    script = [
        'tell application "Reminders"',
        f"set targetReminder to first reminder whose id is {_as_string(uid)}",
    ]
    if title is not None:
        script.append(f"set name of targetReminder to {_as_string(title)}")
    if notes is not None:
        script.append(f"set body of targetReminder to {_as_string(notes)}")
    if due is not None:
        script.append(f"set due date of targetReminder to date {_as_string(due + ' 00:00:00')}")
    script.extend(["return id of targetReminder", "end tell"])
    return _run_osascript("\n".join(script), "reminders.update", args)


def complete_reminder(uid: str) -> str:
    args = {"uid": uid}
    script = "\n".join(
        [
            'tell application "Reminders"',
            f"set targetReminder to first reminder whose id is {_as_string(uid)}",
            "set completed of targetReminder to true",
            "return id of targetReminder",
            "end tell",
        ]
    )
    return _run_osascript(script, "reminders.complete", args)


def delete_reminder(uid: str) -> str:
    args = {"uid": uid}
    script = "\n".join(
        [
            'tell application "Reminders"',
            f"delete first reminder whose id is {_as_string(uid)}",
            f"return {_as_string(uid)}",
            "end tell",
        ]
    )
    return _run_osascript(script, "reminders.delete", args)


def _run_osascript(script: str, tool: str, args: dict[str, Any]) -> str:
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
        value = result.stdout.strip()
        log_tool_call(tool, args, "ok", {"id": value})
        return value
    except Exception as e:
        log_tool_call(tool, args, "error", error=str(e))
        log_error("apple_reminders", str(e), args)
        raise


def _as_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
