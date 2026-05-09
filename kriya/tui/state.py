import datetime
import json
import os
from dataclasses import dataclass
from typing import Literal

from kriya.approvals import list_pending_actions
from kriya.inbox import latest_matching_file, read_file_or_empty
from kriya.utils.errors import read_recent_errors

SurfaceKind = Literal["markdown", "approvals", "errors"]


@dataclass(frozen=True)
class Surface:
    key: str
    title: str
    path: str | None
    kind: SurfaceKind
    mtime: float | None = None


SURFACE_SPECS = [
    ("daily_brief", "Daily Brief", "daily-brief-", "markdown"),
    ("tasks", "Tasks", "tasks-", "markdown"),
    ("groceries", "Groceries", "groceries-", "markdown"),
    ("finance", "Finance", "finance-", "markdown"),
    ("vitals", "Vitals", "vitals-", "markdown"),
    ("email", "Email", "inbox.md", "markdown"),
    ("errors", "Errors", "errors.jsonl", "errors"),
]


def discover_surfaces(state_dir: str = "state") -> list[Surface]:
    surfaces = []
    for key, title, locator, kind in SURFACE_SPECS:
        path = _resolve_surface_path(state_dir, locator)
        surfaces.append(Surface(key=key, title=title, path=path, kind=kind, mtime=_mtime(path)))
    return surfaces


def load_surface(surface: Surface, state_dir: str = "state") -> str:
    if surface.kind == "errors":
        return format_errors(read_recent_errors(state_dir))
    content = read_file_or_empty(surface.path)
    return content or f"# {surface.title}\n\nNo {surface.title.lower()} snapshot found.\n"


def load_approvals(state_dir: str = "state") -> list[dict]:
    return list_pending_actions(state_dir)


def format_errors(errors: list[dict]) -> str:
    if not errors:
        return "# Errors\n\nNo recent errors.\n"
    lines = ["# Errors", ""]
    for error in errors:
        timestamp = error.get("timestamp", "(unknown time)")
        source = error.get("source", "(unknown source)")
        message = error.get("message", "")
        lines.append(f"- **{timestamp}** `{source}`: {message}")
    return "\n".join(lines) + "\n"


def freshness_label(surface: Surface, today: datetime.date | None = None) -> str:
    today = today or datetime.date.today()
    if not surface.path:
        return "--"
    date = _date_from_path(surface.path) or _date_from_mtime(surface.mtime)
    if not date:
        return "?"
    age = (today - date).days
    if age == 0:
        return "ok"
    if age == 1:
        return "old"
    return "stale"


def surface_row_label(surface: Surface, today: datetime.date | None = None) -> str:
    marker = {"ok": "[+]", "old": "[.]", "stale": "[!]", "--": "[ ]", "?": "[?]"}[freshness_label(surface, today)]
    return f"{marker} {surface.title}"


def approval_rows(approvals: list[dict]) -> list[tuple[str, str, str, str]]:
    return [
        (
            item.get("id", "")[:8],
            item.get("tool", ""),
            item.get("intent", ""),
            item.get("status", ""),
        )
        for item in approvals
    ]


def approval_markdown(item: dict | None) -> str:
    if not item:
        return "# Approval\n\nNo approval selected.\n"
    return "\n".join(
        [
            "# Approval",
            "",
            f"- id: `{item.get('id', '')}`",
            f"- status: `{item.get('status', '')}`",
            f"- tool: `{item.get('tool', '')}`",
            f"- intent: {item.get('intent', '')}",
            f"- source: `{item.get('source', '')}`",
            "",
            "## Rationale",
            item.get("rationale", ""),
            "",
            "## Args",
            "```json",
            json.dumps(item.get("args", {}), indent=2, sort_keys=True),
            "```",
        ]
    ) + "\n"


def _resolve_surface_path(state_dir: str, locator: str) -> str | None:
    if locator.endswith(".md") or locator.endswith(".jsonl"):
        path = os.path.join(state_dir, locator)
        return path if os.path.exists(path) else None
    return latest_matching_file(state_dir, locator)


def _mtime(path: str | None) -> float | None:
    if not path or not os.path.exists(path):
        return None
    return os.path.getmtime(path)


def _date_from_path(path: str) -> datetime.date | None:
    name = os.path.basename(path)
    for part in name.removesuffix(".md").split("-"):
        if len(part) == 4 and part.isdigit():
            maybe = "-".join(name.removesuffix(".md").split("-")[-3:])
            try:
                return datetime.date.fromisoformat(maybe)
            except ValueError:
                return None
    return None


def _date_from_mtime(mtime: float | None) -> datetime.date | None:
    if mtime is None:
        return None
    return datetime.datetime.fromtimestamp(mtime).date()
