import json
import subprocess

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error


def get_events(days=1):
    """Returns normalized events from ical CLI, or None if ical is not installed."""
    args = ["today"] if days == 1 else ["upcoming", "-d", str(days)]
    try:
        result = subprocess.run(
            ["ical"] + args + ["-o", "json"],
            capture_output=True, text=True, check=True,
        )
        raw = json.loads(result.stdout)
        events = [_normalize(e) for e in raw]
        log_tool_call("ical." + args[0], {}, "ok", {"count": len(events)})
        return events
    except FileNotFoundError:
        return None
    except Exception as e:
        log_error("apple_calendar", str(e), {"days": days})
        return []


def _normalize(e):
    return {
        "title": e.get("title", "(No Title)"),
        "start": e.get("start_date", ""),
        "all_day": e.get("all_day", False),
        "calendar": e.get("calendar", ""),
    }
