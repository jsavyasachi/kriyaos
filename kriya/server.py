import os
import json
import datetime
import sys

# Add the project root to sys.path to resolve kriya module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from kriya.daily_brief import get_calendar_events, get_unread_emails

# Create an MCP server
mcp = FastMCP("KriyaOS")

@mcp.tool()
def get_daily_brief() -> str:
    """
    Generates a daily brief summary including upcoming calendar events 
    and unread emails (excluding social/promotions).
    """
    today = datetime.date.today().isoformat()
    
    events = get_calendar_events()
    emails = get_unread_emails()
    
    # Format Calendar Section
    calendar_md = ""
    if events:
        for event in events:
            start_raw = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
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

    brief = f"""# Daily Brief: {today}

## 📅 Calendar
{calendar_md}

## 📧 Email
{email_md}

## 💰 Finance
Finance summary placeholder (Integration with f5e pending)
"""
    return brief

if __name__ == "__main__":
    mcp.run()
