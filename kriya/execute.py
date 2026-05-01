"""
Deterministic executor — no LLM in this loop.
Reads an approved pending action, calls the registered tool handler, marks as executed.
"""
import datetime
import json
import os

from kriya.approvals import pending_path
from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error

_TOOLS: dict = {}


def register(name: str):
    def decorator(fn):
        _TOOLS[name] = fn
        return fn
    return decorator


def execute_action(approval_id: str, state_dir: str = "state") -> dict:
    path = pending_path(state_dir, approval_id)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No pending action found: {approval_id}")

    with open(path, encoding="utf-8") as f:
        item = json.load(f)

    if item["status"] == "executed":
        return item
    if item["status"] != "approved":
        raise ValueError(f"Action {approval_id} must be approved before executing (status: {item['status']})")

    tool = item["tool"]
    if tool not in _TOOLS:
        raise ValueError(f"No executor registered for tool: {tool}")

    result = _TOOLS[tool](item["args"])

    item["status"] = "executed"
    item["executed_at"] = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    item["result"] = result

    with open(path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, sort_keys=True)
        f.write("\n")

    log_tool_call(f"execute.{tool}", item["args"], "ok", {"id": approval_id})
    return item


# ---------------------------------------------------------------------------
# Registered write tools
# ---------------------------------------------------------------------------

@register("tasks.insert")
def _insert_task(args: dict) -> dict:
    from kriya.daily_brief import run_gws
    params = {
        "tasklist": args.get("tasklist", "@default"),
        "title": args["title"],
    }
    if args.get("notes"):
        params["notes"] = args["notes"]
    if args.get("due"):
        params["due"] = args["due"]
    return run_gws("tasks.tasks.insert", params)


@register("calendar.create_event")
def _create_calendar_event(args: dict) -> dict:
    from kriya.daily_brief import run_gws

    start = args["start"]
    end = args["end"]
    params = {
        "calendarId": "primary",
        "summary": args["summary"],
        "start": {"dateTime": start} if "T" in start else {"date": start},
        "end": {"dateTime": end} if "T" in end else {"date": end},
    }
    if args.get("description"):
        params["description"] = args["description"]
    if args.get("location"):
        params["location"] = args["location"]

    return run_gws("calendar.events.insert", params)
