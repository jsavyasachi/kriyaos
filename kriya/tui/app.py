import os
import threading
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import DataTable, Footer, Header, Label, ListItem, ListView, Markdown, Static
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from kriya.approvals import approve_action, reject_action
from kriya.poll import format_poll_result, run_poll
from kriya.task_sync import format_task_sync_result, run_task_sync
from kriya.tui.bindings import BINDINGS
from kriya.tui.state import Surface, approval_markdown, approval_rows, discover_surfaces, load_approvals, load_surface, surface_row_label


class RefreshState(Message):
    pass


class _StateChangeHandler(FileSystemEventHandler):
    def __init__(self, app: "KriyaApp") -> None:
        self.app = app
        self._timer: threading.Timer | None = None
        self.active = True

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(0.2, self._post_refresh)
        self._timer.daemon = True
        self._timer.start()

    def _post_refresh(self) -> None:
        if not self.active:
            return
        try:
            self.app.call_from_thread(self.app.post_message, RefreshState())
        except RuntimeError:
            pass


class KriyaApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    #rail {
        width: 28;
        border: solid $primary;
    }

    #detail {
        width: 1fr;
        border: solid $secondary;
    }

    #approvals {
        height: 12;
        border: solid $accent;
    }

    #approval-preview {
        height: 10;
        border: solid $accent;
    }

    #status {
        height: 1;
        padding: 0 1;
    }
    """

    BINDINGS = BINDINGS

    def __init__(self, state_dir: str = "state", watch: bool = True) -> None:
        super().__init__()
        self.state_dir = state_dir
        self.watch = watch
        self.surfaces: list[Surface] = []
        self.approvals: list[dict[str, Any]] = []
        self._observer: Observer | None = None
        self._watch_handler: _StateChangeHandler | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            yield ListView(id="rail")
            yield Markdown("# Kriya OS\n\nLoading state...", id="detail")
        with Vertical(id="approvals"):
            yield Label("Approvals")
            yield DataTable(id="approval-table")
        yield Markdown("# Approval\n\nNo approval selected.", id="approval-preview")
        yield Static("Ready", id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#approval-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("id", "tool", "intent", "status")
        self.refresh_state()
        self._start_watcher()

    def on_unmount(self) -> None:
        self._stop_watcher()

    def on_refresh_state(self, _message: RefreshState) -> None:
        self.refresh_state()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        rail = self.query_one("#rail", ListView)
        index = rail.index
        if index is None or index >= len(self.surfaces):
            return
        self.show_surface(self.surfaces[index])

    def on_data_table_row_selected(self, _event: DataTable.RowSelected) -> None:
        self.preview_selected_approval()

    def action_select_or_preview(self) -> None:
        focused = self.focused
        if isinstance(focused, DataTable):
            self.preview_selected_approval()
        elif isinstance(focused, ListView):
            focused.action_select_cursor()

    def action_reload_or_reject(self) -> None:
        if isinstance(self.focused, DataTable):
            self.action_reject_approval()
        else:
            self.refresh_state("Reloaded")

    def action_approve_approval(self) -> None:
        item = self.selected_approval()
        if not item:
            self.set_status("No approval selected")
            return
        if item.get("status") != "pending":
            self.set_status(f"Approval {item.get('id', '')[:8]} is not pending")
            return
        approve_action(item["id"], self.state_dir)
        self.refresh_state(f"Approved {item['id'][:8]}")

    def action_reject_approval(self) -> None:
        item = self.selected_approval()
        if not item:
            self.set_status("No approval selected")
            return
        if item.get("status") not in {"pending", "approved"}:
            self.set_status(f"Approval {item.get('id', '')[:8]} cannot be rejected")
            return
        reject_action(item["id"], self.state_dir)
        self.refresh_state(f"Rejected {item['id'][:8]}")

    def action_execute_approval(self) -> None:
        item = self.selected_approval()
        if not item:
            self.set_status("No approval selected")
            return
        if item.get("status") != "approved":
            self.set_status(f"Approval {item.get('id', '')[:8]} must be approved first")
            return
        self.execute_approval(item["id"])

    def action_poll(self) -> None:
        self.run_poll_worker()

    def action_sync_tasks(self) -> None:
        self.run_sync_worker()

    def refresh_state(self, status: str | None = None) -> None:
        self.surfaces = discover_surfaces(self.state_dir)
        self.approvals = load_approvals(self.state_dir)
        self.refresh_rail()
        self.refresh_approvals()
        if self.surfaces:
            index = self.query_one("#rail", ListView).index or 0
            self.show_surface(self.surfaces[min(index, len(self.surfaces) - 1)])
        if status:
            self.set_status(status)

    def refresh_rail(self) -> None:
        rail = self.query_one("#rail", ListView)
        rail.clear()
        for surface in self.surfaces:
            rail.append(ListItem(Label(surface_row_label(surface))))
        if self.surfaces and rail.index is None:
            rail.index = 0

    def refresh_approvals(self) -> None:
        table = self.query_one("#approval-table", DataTable)
        table.clear(columns=False)
        for row in approval_rows(self.approvals):
            table.add_row(*row)
        self.preview_selected_approval()

    def show_surface(self, surface: Surface) -> None:
        detail = self.query_one("#detail", Markdown)
        detail.update(load_surface(surface, self.state_dir))

    def selected_approval(self) -> dict[str, Any] | None:
        table = self.query_one("#approval-table", DataTable)
        if table.row_count == 0:
            return None
        row = table.cursor_row
        if row < 0 or row >= len(self.approvals):
            return None
        return self.approvals[row]

    def preview_selected_approval(self) -> None:
        preview = self.query_one("#approval-preview", Markdown)
        preview.update(approval_markdown(self.selected_approval()))

    def set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    @work(thread=True, exclusive=True, group="poll")
    def run_poll_worker(self) -> None:
        self.call_from_thread(self.set_status, "Polling...")
        result = run_poll(state_dir=self.state_dir)
        self.call_from_thread(self.set_status, format_poll_result(result).splitlines()[0])
        self.call_from_thread(self.post_message, RefreshState())

    @work(thread=True, exclusive=True, group="sync")
    def run_sync_worker(self) -> None:
        self.call_from_thread(self.set_status, "Syncing tasks...")
        result = run_task_sync(state_dir=self.state_dir)
        self.call_from_thread(self.set_status, format_task_sync_result(result).splitlines()[0])
        self.call_from_thread(self.post_message, RefreshState())

    @work(thread=True, exclusive=True, group="execute")
    def execute_approval(self, approval_id: str) -> None:
        self.call_from_thread(self.set_status, f"Executing {approval_id[:8]}...")
        import kriya.google_tasks  # noqa: F401
        from kriya.execute import execute_action

        execute_action(approval_id, self.state_dir)
        self.call_from_thread(self.set_status, f"Executed {approval_id[:8]}")
        self.call_from_thread(self.post_message, RefreshState())

    def _start_watcher(self) -> None:
        if not self.watch or not os.path.exists(self.state_dir):
            return
        handler = _StateChangeHandler(self)
        observer = Observer()
        observer.schedule(handler, self.state_dir, recursive=True)
        observer.daemon = True
        observer.start()
        self._observer = observer
        self._watch_handler = handler

    def _stop_watcher(self) -> None:
        if self._watch_handler:
            self._watch_handler.active = False
            if self._watch_handler._timer:
                self._watch_handler._timer.cancel()
            self._watch_handler = None
        if not self._observer:
            return
        self._observer.stop()
        self._observer.join(timeout=2)
        self._observer = None


def run_tui(state_dir: str = "state") -> None:
    KriyaApp(state_dir=state_dir).run()
