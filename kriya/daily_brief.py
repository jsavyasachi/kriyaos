import subprocess
import json
import datetime
import os

def get_calendar_events(max_results=10):
    """Fetches calendar events using gws CLI, starting from today."""
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    params = {
        "calendarId": "primary",
        "maxResults": max_results,
        "timeMin": now,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    cmd = ["gws", "calendar", "events", "list", "--params", json.dumps(params)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        events = data.get("items", [])
        return events
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return []

def get_unread_emails(max_results=5):
    """Fetches unread emails using gws CLI."""
    # Filter out promotions and social to get "real" emails
    q = "is:unread -category:social -category:promotions"
    cmd = ["gws", "gmail", "users", "messages", "list", "--params", json.dumps({"userId": "me", "maxResults": max_results, "q": q})]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        message_summaries = data.get("messages", [])
        
        emails = []
        for summary in message_summaries:
            msg_id = summary["id"]
            # Get full message details
            get_cmd = ["gws", "gmail", "users", "messages", "get", "--params", json.dumps({"userId": "me", "id": msg_id})]
            get_result = subprocess.run(get_cmd, capture_output=True, text=True, check=True)
            msg_data = json.loads(get_result.stdout)
            
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
        print(f"Error fetching emails: {e}")
        return []

def generate_daily_brief():
    today = datetime.date.today().isoformat()
    state_dir = "state"
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)
    
    brief_path = os.path.join(state_dir, f"daily-brief-{today}.md")
    
    print(f"Generating brief for {today}...")
    
    events = get_calendar_events()
    emails = get_unread_emails()
    
    # Format Calendar Section
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
        
    # Format Email Section
    email_md = ""
    if emails:
        for email in emails:
            email_md += f"- **{email['from']}**: {email['subject']}\n  - *{email['snippet']}*\n"
    else:
        email_md = "No unread emails found.\n"

    finance_data = "Finance summary placeholder (Integration with f5e pending)"
    
    content = f"""# Daily Brief: {today}

## 📅 Calendar
{calendar_md}

## 📧 Email
{email_md}

## 💰 Finance
{finance_data}
"""
    
    with open(brief_path, "w") as f:
        f.write(content)
    
    print(f"Brief written to {brief_path}")

if __name__ == "__main__":
    generate_daily_brief()
