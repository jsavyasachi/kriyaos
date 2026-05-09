import datetime
import os
from typing import Any

from kriya.apple_reminders import get_reminders_for_list
from kriya.sync_routes import get_sync_route

GROCERY_ROUTE = get_sync_route("groceries")


def get_groceries() -> list[dict[str, Any]]:
    return get_reminders_for_list(GROCERY_ROUTE["apple"]["list"]) or []


def format_groceries(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No groceries found.\n"

    lines = []
    for item in items:
        marker = "[x]" if item.get("completed") else "[ ]"
        lines.append(f"- {marker} {item.get('title', '(No Title)')}")
    return "\n".join(lines) + "\n"


def write_groceries_snapshot(state_dir: str = "state", today: str | None = None) -> str:
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)
    content = f"# Groceries: {today}\n\n{format_groceries(get_groceries())}"
    path = os.path.join(state_dir, f"groceries-{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Groceries snapshot written to {path}")
    return path
