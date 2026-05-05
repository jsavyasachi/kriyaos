import datetime
import os
from typing import Any

from kriya.daily_brief import run_gws
from kriya.utils.errors import log_error


def get_notes(page_size: int = 20, state_dir: str = "state") -> list[dict[str, Any]]:
    params = {"pageSize": page_size}
    try:
        data = run_gws("keep.notes.list", params)
        return data.get("notes", [])
    except Exception as e:
        log_error("keep.notes", str(e), {"page_size": page_size}, state_dir)
        raise


def _body_text(note: dict[str, Any]) -> str:
    body = note.get("body", {})
    text = body.get("text", {}).get("text") or body.get("textContent", {}).get("text")
    if text:
        return text.strip()

    list_items = body.get("list", {}).get("listItems") or body.get("listContent", {}).get("listItems") or []
    lines = []
    for item in list_items:
        item_text = item.get("text", {}).get("text") or item.get("textContent", {}).get("text")
        if not item_text:
            continue
        prefix = "[x]" if item.get("checked") else "[ ]"
        lines.append(f"{prefix} {item_text.strip()}")
    return "\n".join(lines)


def format_notes(notes: list[dict[str, Any]]) -> str:
    if not notes:
        return "No notes found.\n"

    lines = []
    for note in notes:
        title = note.get("title") or "(Untitled)"
        updated = note.get("updateTime", "")
        updated_label = f" updated {updated.split('T')[0]}" if updated else ""
        lines.append(f"- **{title}**{updated_label}")
        body = _body_text(note)
        if body:
            for line in body.splitlines():
                lines.append(f"  - {line}")
    return "\n".join(lines) + "\n"


def get_notes_section(page_size: int = 20, state_dir: str = "state") -> str | None:
    try:
        return format_notes(get_notes(page_size=page_size, state_dir=state_dir))
    except Exception:
        return None


def write_notes_snapshot(state_dir: str = "state", today: str | None = None, page_size: int = 20) -> str:
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)
    notes_md = get_notes_section(page_size=page_size, state_dir=state_dir) or "Notes unavailable.\n"
    content = f"# Notes: {today}\n\n{notes_md}"
    path = os.path.join(state_dir, f"notes-{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Notes snapshot written to {path}")
    return path
