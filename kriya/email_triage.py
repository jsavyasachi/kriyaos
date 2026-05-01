import datetime
import json
import os
import re

from kriya.approvals import create_pending_action
from kriya.daily_brief import get_unread_emails


CATEGORIES = ("urgent", "normal", "newsletter", "automated")

URGENT_TERMS = (
    "urgent",
    "asap",
    "action required",
    "security alert",
    "verify",
    "failed",
    "failure",
    "overdue",
    "deadline",
)

NEWSLETTER_TERMS = (
    "newsletter",
    "digest",
    "roundup",
    "weekly",
    "monthly",
    "unsubscribe",
)

AUTOMATED_SENDERS = (
    "no-reply",
    "noreply",
    "donotreply",
    "do-not-reply",
    "notification",
    "receipts",
)

AUTOMATED_TERMS = (
    "receipt",
    "confirmation",
    "invoice",
    "statement",
    "alert",
    "code",
    "otp",
)

MEETING_TERMS = (
    "meet",
    "meeting",
    "call",
    "sync",
    "catch up",
    "catchup",
    "standup",
    "stand-up",
    "zoom",
    "google meet",
    "teams call",
    "interview",
    "calendar invite",
    "schedule time",
    "book a time",
    "find a time",
    "availability",
    "let's connect",
    "lets connect",
)

ACTION_TERMS = (
    "please",
    "can you",
    "could you",
    "need",
    "needs",
    "follow up",
    "reply",
    "respond",
    "review",
    "send",
    "schedule",
    "book",
    "confirm",
    "approve",
    "action required",
)


def classify_email(email):
    text = " ".join(
        [
            email.get("from", ""),
            email.get("subject", ""),
            email.get("snippet", ""),
        ]
    ).lower()

    if any(term in text for term in URGENT_TERMS):
        return "urgent"
    if any(term in text for term in NEWSLETTER_TERMS):
        return "newsletter"
    if any(term in text for term in AUTOMATED_SENDERS + AUTOMATED_TERMS):
        return "automated"
    return "normal"


def triage_emails(emails):
    triaged = {category: [] for category in CATEGORIES}
    for email in emails:
        triaged[classify_email(email)].append(email)
    return triaged


def email_source(email):
    return "email:" + "|".join(
        [
            email.get("from", ""),
            email.get("subject", ""),
            email.get("snippet", ""),
        ]
    )


def is_actionable_email(email, category):
    text = " ".join(
        [
            email.get("subject", ""),
            email.get("snippet", ""),
        ]
    ).lower()
    if category == "urgent":
        return True
    return category == "normal" and any(term in text for term in ACTION_TERMS)


def is_meeting_request(email):
    text = " ".join([
        email.get("subject", ""),
        email.get("snippet", ""),
    ]).lower()
    return any(term in text for term in MEETING_TERMS)


def _next_business_day_9am():
    d = datetime.date.today() + datetime.timedelta(days=1)
    while d.weekday() >= 5:  # skip weekend
        d += datetime.timedelta(days=1)
    return datetime.datetime.combine(d, datetime.time(9, 0))


def extract_event_times(email):
    """Best-effort time extraction from email text. Returns (start_iso, end_iso)."""
    text = " ".join([email.get("subject", ""), email.get("snippet", "")])
    try:
        from dateutil import parser as du_parser
        from dateutil.parser import ParserError

        # Look for date-like fragments: "May 5", "tomorrow", "next Monday", "5/12 at 3pm"
        patterns = [
            r"(?:tomorrow|today)",
            r"next\s+\w+day",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:\s+at\s+[\d:apm ]+)?",
            r"\b\d{1,2}/\d{1,2}(?:\s+at\s+[\d:apm ]+)?",
            r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*(?:\s+at\s+[\d:apm ]+)?",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                candidate = m.group(0)
                try:
                    start = du_parser.parse(candidate, default=_next_business_day_9am(), fuzzy=True)
                    if start < datetime.datetime.now():
                        start = _next_business_day_9am()
                    end = start + datetime.timedelta(hours=1)
                    return start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S")
                except (ParserError, OverflowError):
                    continue
    except ImportError:
        pass

    start = _next_business_day_9am()
    return start.strftime("%Y-%m-%dT%H:%M:%S"), (start + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")


def create_event_proposals(triaged, state_dir="state"):
    paths = []
    for category, emails in triaged.items():
        for email in emails:
            if category not in ("urgent", "normal"):
                continue
            if not is_meeting_request(email):
                continue
            subject = email.get("subject", "(No Subject)")
            sender = email.get("from", "(Unknown Sender)")
            snippet = email.get("snippet", "")
            start, end = extract_event_times(email)
            args = {
                "summary": subject,
                "start": start,
                "end": end,
                "description": f"From: {sender}\n\n{snippet}".strip(),
            }
            path = create_pending_action(
                "calendar.create_event",
                args,
                f"Email from {sender} appears to be a meeting request.",
                email_source(email),
                f"schedule: {subject}",
                state_dir,
            )
            paths.append(path)
    return paths


def create_task_proposals(triaged, state_dir="state"):
    paths = []
    for category, emails in triaged.items():
        for email in emails:
            if not is_actionable_email(email, category):
                continue
            subject = email.get("subject", "(No Subject)")
            sender = email.get("from", "(Unknown Sender)")
            snippet = email.get("snippet", "")
            title = f"Follow up: {subject}"
            notes = f"From: {sender}\n\n{snippet}".strip()
            path = create_pending_action(
                "tasks.insert",
                {"tasklist": "@default", "title": title, "notes": notes},
                "Unread email appears actionable; create a Google Task only after approval.",
                email_source(email),
                title,
                state_dir,
            )
            paths.append(path)
    return paths


def format_triage(today, triaged):
    lines = [f"## Email Triage: {today}", ""]
    for category in CATEGORIES:
        emails = triaged.get(category, [])
        lines.append(f"### {category.title()} ({len(emails)})")
        if emails:
            for email in emails:
                sender = email.get("from", "(Unknown Sender)")
                subject = email.get("subject", "(No Subject)")
                snippet = email.get("snippet", "")
                lines.append(f"- **{sender}**: {subject}")
                if snippet:
                    lines.append(f"  - {snippet}")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run_marker_path(state_dir, today):
    return os.path.join(state_dir, "runs", f"{today}-email_triage.json")


def write_run_marker(state_dir, today, inbox_path):
    runs_dir = os.path.join(state_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    marker = {
        "completed_at": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "date": today,
        "skill": "email_triage",
        "status": "completed",
        "inbox_path": inbox_path,
    }
    with open(run_marker_path(state_dir, today), "w", encoding="utf-8") as f:
        json.dump(marker, f, indent=2, sort_keys=True)
        f.write("\n")


def append_email_triage(state_dir="state", today=None, max_results=10, force=False):
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)

    inbox_path = os.path.join(state_dir, "inbox.md")
    marker_path = run_marker_path(state_dir, today)
    if not force and os.path.exists(marker_path):
        print(f"Email triage already generated for {today}; skipping.")
        return inbox_path

    emails = get_unread_emails(max_results=max_results)
    triaged = triage_emails(emails)
    task_paths = create_task_proposals(triaged, state_dir)
    event_paths = create_event_proposals(triaged, state_dir)
    content = format_triage(today, triaged)

    with open(inbox_path, "a", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")
    write_run_marker(state_dir, today, inbox_path)

    print(f"Email triage appended to {inbox_path}; proposed {len(task_paths)} task(s), {len(event_paths)} event(s).")
    return inbox_path


if __name__ == "__main__":
    append_email_triage()
