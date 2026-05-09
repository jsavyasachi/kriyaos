from textual.binding import Binding

BINDINGS = [
    Binding("q", "quit", "Quit"),
    Binding("?", "help", "Help"),
    Binding("r", "reload_or_reject", "Reload/Reject"),
    Binding("tab", "focus_next", "Next focus"),
    Binding("enter", "select_or_preview", "Select"),
    Binding("a", "approve_approval", "Approve"),
    Binding("x", "execute_approval", "Execute"),
    Binding("p", "poll", "Poll"),
    Binding("s", "sync_tasks", "Sync tasks"),
]
