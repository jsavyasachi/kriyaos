from typing import Any

SYNC_ROUTES: dict[str, dict[str, Any]] = {
    "tasks.todo": {
        "google": {"service": "tasks", "list": "To Do"},
        "apple": {"service": "reminders", "list": "To do"},
    },
    "groceries": {
        "apple": {"service": "reminders", "list": "Groceries"},
        "mode": "apple_only",
        "unsupported_google_source": "Google Keep scope is rejected for the current @gmail.com OAuth client",
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
