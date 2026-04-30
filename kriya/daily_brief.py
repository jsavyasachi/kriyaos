import subprocess
import json
import datetime
import os

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
    except Exception as e:
        log_tool_call(f"gws.{tool}", params, "error", error=str(e))
        raise

def get_calendar_events(max_results=10):
    """Fetches calendar events using gws CLI, starting from today."""
    # Use timezone-aware UTC datetime
    now = datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00', 'Z')
    params = {
        "calendarId": "primary",
        "maxResults": max_results,
        "timeMin": now,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    try:
        data = run_gws("calendar.events.list", params)
        events = data.get("items", [])
        return events
    except Exception as e:
        message = f"Error fetching calendar: {e}"
        print(message)
        log_error("daily_brief.calendar", str(e), {"max_results": max_results})
        return []

def get_unread_emails(max_results=5):
    """Fetches unread emails using gws CLI."""
    # Filter out promotions and social to get "real" emails
    q = "is:unread -category:social -category:promotions"
    params = {"userId": "me", "maxResults": max_results, "q": q}
    try:
        data = run_gws("gmail.users.messages.list", params)
        message_summaries = data.get("messages", [])
        
        emails = []
        for summary in message_summaries:
            msg_id = summary["id"]
            # Get full message details
            msg_data = run_gws("gmail.users.messages.get", {"userId": "me", "id": msg_id})
            
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
    except Exception as e:
        message = f"Error fetching emails: {e}"
        print(message)
        log_error("daily_brief.email", str(e), {"max_results": max_results})
        return []


def format_calendar(events):
    calendar_md = ""
    if events:
        for event in events:
            start_raw = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            # Simple cleanup of ISO format for readability
            start = start_raw.split('T')[0] if 'T' in start_raw else start_raw
            time = start_raw.split('T')[1][:5] if 'T' in start_raw else "All Day"
            
            summary = event.get("summary", "(No Title)")
            calendar_md += f"- **{start} {time}**: {summary}\n"
    else:
        calendar_md = "No upcoming events found.\n"
    return calendar_md


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


def build_daily_brief(today, events, emails, errors=None):
    finance_data = "Finance summary placeholder (Integration with f5e pending)"
    calendar_md = format_calendar(events)
    email_md = format_email(emails)
    error_md = format_errors(errors or [])

    return f"""# Daily Brief: {today}

## 📅 Calendar
{calendar_md}

## 📧 Email
{email_md}

## 💰 Finance
{finance_data}

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

    events = get_calendar_events()
    emails = get_unread_emails()
    errors = read_recent_errors(state_dir)
    content = build_daily_brief(today, events, emails, errors)

    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(content)
    write_run_marker(state_dir, today, brief_path)

    print(f"Brief written to {brief_path}")
    return brief_path

if __name__ == "__main__":
    generate_daily_brief()
