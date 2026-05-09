from typing import Any

SYNC_ROUTES: dict[str, dict[str, Any]] = {
    "tasks.todo": {
        "google": {"service": "tasks", "list": "To Do"},
        "apple": {"service": "reminders", "list": "To do"},
    },
    "groceries": {
        "google": {"service": "keep", "note": "Groceries"},
        "apple": {"service": "reminders", "list": "Groceries"},
        "blocked_by": "Google Keep OAuth scope",
    },
    "reminders": {
        "apple": {"service": "reminders", "list": "Reminders"},
        "mode": "apple_only",
    },
}


def get_sync_route(name: str) -> dict[str, Any]:
    try:
        return SYNC_ROUTES[name]
    except KeyError as e:
        raise ValueError(f"Unknown sync route: {name}") from e
