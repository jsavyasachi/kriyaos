import datetime
import os
from typing import Any

from kriya.daily_brief import run_gws
from kriya.execute import register
from kriya.utils.errors import log_error


def get_notes(page_size: int = 20, state_dir: str = "state") -> list[dict[str, Any]]:
    params = {"pageSize": page_size}
    try:
        data = run_gws("keep.notes.list", params)
        return data.get("notes", [])
    except Exception as e:
        log_error("keep.notes", str(e), {"page_size": page_size}, state_dir)
        raise


def get_note_by_title(title: str, page_size: int = 100, state_dir: str = "state") -> dict[str, Any] | None:
    for note in get_notes(page_size=page_size, state_dir=state_dir):
        if note.get("title") == title:
            if note.get("name"):
                return run_gws("keep.notes.get", {"name": note["name"]})
            return note
    return None


def get_grocery_items(note_title: str = "Groceries", state_dir: str = "state") -> dict[str, Any] | None:
    note = get_note_by_title(note_title, state_dir=state_dir)
    if note is None:
        return None
    return {
        "name": note.get("name"),
        "title": note.get("title", note_title),
        "updated": note.get("updateTime"),
        "items": normalize_keep_list_items(note),
    }


def normalize_keep_list_items(note: dict[str, Any]) -> list[dict[str, Any]]:
    list_items = note.get("body", {}).get("list", {}).get("listItems")
    list_items = list_items or note.get("body", {}).get("listContent", {}).get("listItems") or []
    items = []
    for index, item in enumerate(list_items):
        title = item.get("text", {}).get("text") or item.get("textContent", {}).get("text")
        if not title:
            continue
        items.append(
            {
                "id": item.get("name") or item.get("id") or f"keep-{index}",
                "title": title.strip(),
                "completed": bool(item.get("checked", False)),
                "updated": note.get("updateTime"),
            }
        )
    return items


@register("keep.replace_note")
def replace_note(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("name"):
        run_gws("keep.notes.delete", {"name": args["name"]})
    return run_gws("keep.notes.create", _keep_note_body(args.get("title", "Groceries"), args.get("items", [])))


def _keep_note_body(title: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": title,
        "body": {
            "list": {
                "listItems": [
                    {
                        "text": {"text": item.get("title", "")},
                        "checked": bool(item.get("completed", False)),
                    }
                    for item in items
                    if item.get("title")
                ]
            }
        },
    }


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
