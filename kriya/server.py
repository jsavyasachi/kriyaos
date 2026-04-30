import datetime
import os
import sys

# Add the project root to sys.path to resolve kriya module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.server.fastmcp import FastMCP
from kriya.daily_brief import build_daily_brief, get_calendar_events, get_unread_emails

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
    return build_daily_brief(today, events, emails)

if __name__ == "__main__":
    mcp.run()
