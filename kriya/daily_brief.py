import subprocess
import json
import datetime
import os
import contextlib
import io

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error, read_recent_errors
from kriya.utils.usage import cost_ceiling_reached, daily_spend_usd, parse_daily_limit


def run_gws(tool, params):
    cmd = ["gws", *tool.split("."), "--params", json.dumps(params)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        summary = {"type": type(data).__name__}
        if isinstance(data, dict):
            if "items" in data:
                summary["count"] = len(data.get("items", []))
            if "messages" in data:
                summary["count"] = len(data.get("messages", []))
            if "id" in data:
                summary["id"] = data.get("id")
        log_tool_call(f"gws.{tool}", params, "ok", summary)
        return data
    except FileNotFoundError as e:
        message = "gws CLI not found on PATH"
        log_tool_call(f"gws.{tool}", params, "error", error=message)
        raise RuntimeError(message) from e
    except Exception as e:
        log_tool_call(f"gws.{tool}", params, "error", error=str(e))
        raise

def _normalize_google_event(event):
    start = event.get("start", {})
    start_raw = start.get("dateTime") or start.get("date", "")
    return {
        "title": event.get("summary", "(No Title)"),
        "start": start_raw,
        "all_day": "dateTime" not in start,
    }


def get_calendar_events(max_results=10):
    """Fetches today's calendar events. Tries ical (Apple Calendar) first, falls back to gws."""
    from kriya.apple_calendar import get_events as get_apple_events
    apple_events = get_apple_events(days=1)
    if apple_events is not None:
        return apple_events

    now = datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00', 'Z')
    params = {
        "calendarId": "primary",
        "maxResults": max_results,
        "timeMin": now,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    try:
        data = run_gws("calendar.events.list", params)
    except Exception as e:
        log_error("daily_brief.calendar", str(e), {"max_results": max_results})
        raise
    return [_normalize_google_event(e) for e in data.get("items", [])]

def get_unread_emails(max_results=5):
    """Fetches unread emails using gws CLI."""
    # Filter out promotions and social to get "real" emails
    q = "is:unread -category:social -category:promotions"
    params = {"userId": "me", "maxResults": max_results, "q": q}
    try:
        data = run_gws("gmail.users.messages.list", params)
    except Exception as e:
        log_error("daily_brief.email", str(e), {"max_results": max_results})
        raise

    emails = []
    for summary in data.get("messages", []):
        msg_id = summary["id"]
        try:
            msg_data = run_gws("gmail.users.messages.get", {"userId": "me", "id": msg_id})
        except Exception as e:
            log_error("daily_brief.email", str(e), {"message_id": msg_id})
            raise

        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")
        snippet = msg_data.get("snippet", "")

        emails.append({
            "subject": subject,
            "from": sender,
            "snippet": snippet
        })
    return emails


def format_calendar(events):
    if not events:
        return "No upcoming events found.\n"
    lines = []
    for event in events:
        start_raw = event.get("start", "")
        if event.get("all_day") or "T" not in start_raw:
            date, time_str = start_raw, "All Day"
        else:
            date = start_raw.split("T")[0]
            time_str = start_raw.split("T")[1][:5]
        lines.append(f"- **{date} {time_str}**: {event.get('title', '(No Title)')}")
    return "\n".join(lines) + "\n"


def format_email(emails):
    email_md = ""
    if emails:
        for email in emails:
            email_md += f"- **{email['from']}**: {email['subject']}\n  - *{email['snippet']}*\n"
    else:
        email_md = "No unread emails found.\n"
    return email_md


def format_errors(errors):
    if not errors:
        return "No recent errors logged.\n"

    error_md = ""
    for error in errors:
        timestamp = error.get("timestamp", "(unknown time)")
        source = error.get("source", "(unknown source)")
        message = error.get("message", "")
        error_md += f"- **{timestamp}** `{source}`: {message}\n"
    return error_md


def get_daily_memories_md(state_dir: str = "state") -> str | None:
    from kriya.memory import format_memories, search as search_memories

    try:
        with contextlib.redirect_stderr(io.StringIO()):
            return format_memories(search_memories("daily preferences context notes", limit=5))
    except Exception as e:
        log_error("daily_brief.memory", str(e), {}, state_dir)
        return None


def build_daily_brief(
    today,
    events,
    emails,
    errors=None,
    tasks_md=None,
    memories_md=None,
    finance_md=None,
    vitals_md=None,
):
    calendar_md = format_calendar(events)
    email_md = format_email(emails)
    error_md = format_errors(errors or [])
    tasks_md = tasks_md or "No open tasks found.\n"
    finance_md = finance_md or "Finance unavailable.\n"
    vitals_md = vitals_md or "Vitals unavailable.\n"

    memory_section = f"\n## 🧠 Memory\n{memories_md}" if memories_md else ""

    return f"""# Daily Brief: {today}
{memory_section}
## 📅 Calendar
{calendar_md}
## 📧 Email
{email_md}
## ✅ Tasks
{tasks_md}
## 💰 Finance
{finance_md}
## ❤️ Vitals
{vitals_md}

## ⚠️ Errors
{error_md}
"""


def run_marker_path(state_dir, today):
    return os.path.join(state_dir, "runs", f"{today}-daily_brief.json")


def write_run_marker(state_dir, today, brief_path):
    runs_dir = os.path.join(state_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    marker = {
        "completed_at": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "date": today,
        "skill": "daily_brief",
        "status": "completed",
        "brief_path": brief_path,
    }
    with open(run_marker_path(state_dir, today), "w", encoding="utf-8") as f:
        json.dump(marker, f, indent=2, sort_keys=True)
        f.write("\n")


def generate_daily_brief(state_dir="state", today=None, force=False):
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)

    brief_path = os.path.join(state_dir, f"daily-brief-{today}.md")
    marker_path = run_marker_path(state_dir, today)

    if not force and os.path.exists(marker_path):
        print(f"Daily brief already generated for {today}; skipping.")
        return brief_path

    daily_limit_usd = parse_daily_limit(os.environ.get("MAX_DAILY_USD"))
    spend_usd = daily_spend_usd(today, state_dir)
    if not force and cost_ceiling_reached(today, state_dir, daily_limit_usd):
        message = f"Daily spend ${spend_usd:.2f} reached limit ${daily_limit_usd:.2f}; skipping daily brief."
        print(message)
        log_error(
            "daily_brief.cost_ceiling",
            message,
            {"date": today, "limit_usd": daily_limit_usd, "spend_usd": spend_usd},
            state_dir,
        )
        return brief_path

    print(f"Generating brief for {today}...")

    from kriya.google_tasks import format_tasks, get_open_tasks
    from kriya.apple_reminders import get_reminders_by_list
    from kriya.finance import format_finance_section, get_networth_report
    from kriya.vitals import format_vitals_section, get_vitals_summary

    events = get_calendar_events()
    emails = get_unread_emails()
    tasks_by_list = get_open_tasks()
    reminders = get_reminders_by_list()
    if reminders:
        tasks_by_list = tasks_by_list + reminders
    tasks_md = format_tasks(tasks_by_list, today)
    errors = read_recent_errors(state_dir)
    memories_md = get_daily_memories_md(state_dir)
    finance_md = format_finance_section(get_networth_report(state_dir=state_dir))
    vitals_md = format_vitals_section(get_vitals_summary(today=today, state_dir=state_dir))
    content = build_daily_brief(today, events, emails, errors, tasks_md, memories_md, finance_md, vitals_md)

    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(content)
    write_run_marker(state_dir, today, brief_path)

    print(f"Brief written to {brief_path}")
    return brief_path

if __name__ == "__main__":
    generate_daily_brief()
