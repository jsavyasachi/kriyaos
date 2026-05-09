import datetime
from typing import Any

from kriya.daily_brief import run_gws
from kriya.execute import register
from kriya.utils.errors import log_error


def get_events_for_sync(window_back: int = 30, window_forward: int = 90) -> list[dict[str, Any]]:
    now = datetime.datetime.now(datetime.UTC)
    params = {
        "calendarId": "primary",
        "timeMin": (now - datetime.timedelta(days=window_back)).isoformat().replace("+00:00", "Z"),
        "timeMax": (now + datetime.timedelta(days=window_forward)).isoformat().replace("+00:00", "Z"),
        "singleEvents": True,
        "orderBy": "startTime",
        "showDeleted": True,
        "maxResults": 2500,
    }
    try:
        data = run_gws("calendar.events.list", params)
    except Exception as e:
        log_error("calendar.events", str(e), {"window_back": window_back, "window_forward": window_forward})
        raise
    return [
        normalize_event_for_sync(event)
        for event in data.get("items", [])
        if not _is_recurring_event(event)
    ]


def normalize_event_for_sync(event: dict[str, Any]) -> dict[str, Any]:
    start = event.get("start", {})
    end = event.get("end", {})
    all_day = "dateTime" not in start
    return {
        "id": event.get("id"),
        "title": event.get("summary", ""),
        "start": start.get("date") if all_day else start.get("dateTime"),
        "end": end.get("date") if all_day else end.get("dateTime"),
        "all_day": all_day,
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "deleted": event.get("status") == "cancelled",
        "updated": event.get("updated"),
    }


@register("calendar.insert")
def insert_event(args: dict[str, Any]) -> dict[str, Any]:
    return run_gws("calendar.events.insert", _event_params(args))


@register("calendar.update")
def update_event(args: dict[str, Any]) -> dict[str, Any]:
    params = {
        "calendarId": args.get("calendarId", "primary"),
        "event": args["id"],
    }
    params.update(_event_body(args))
    return run_gws("calendar.events.patch", params)


@register("calendar.delete")
def delete_event(args: dict[str, Any]) -> dict[str, Any]:
    return run_gws(
        "calendar.events.delete",
        {
            "calendarId": args.get("calendarId", "primary"),
            "event": args["id"],
        },
    )


def _event_params(args: dict[str, Any]) -> dict[str, Any]:
    params = {"calendarId": args.get("calendarId", "primary")}
    params.update(_event_body(args))
    return params


def _event_body(args: dict[str, Any]) -> dict[str, Any]:
    title = args.get("title", args.get("summary", ""))
    body: dict[str, Any] = {
        "summary": title,
        "start": _google_time(args.get("start"), args.get("all_day", False)),
        "end": _google_time(args.get("end"), args.get("all_day", False)),
    }
    if args.get("description"):
        body["description"] = args["description"]
    if args.get("location"):
        body["location"] = args["location"]
    return body


def _google_time(value: str | None, all_day: bool) -> dict[str, str]:
    if all_day:
        return {"date": value or ""}
    return {"dateTime": value or ""}


def _is_recurring_event(event: dict[str, Any]) -> bool:
    return bool(event.get("recurringEventId") or event.get("recurrence"))
