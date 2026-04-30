import datetime
import json
import os

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
    content = format_triage(today, triaged)

    with open(inbox_path, "a", encoding="utf-8") as f:
        f.write(content)
        f.write("\n")
    write_run_marker(state_dir, today, inbox_path)

    print(f"Email triage appended to {inbox_path}")
    return inbox_path


if __name__ == "__main__":
    append_email_triage()
