import datetime
import json
import os
import tempfile
import unittest

from kriya.approvals import create_pending_action
from kriya.tui.state import (
    Surface,
    approval_markdown,
    approval_rows,
    discover_surfaces,
    freshness_label,
    load_approvals,
    load_surface,
    surface_row_label,
)


class TestTuiState(unittest.TestCase):
    def test_discover_surfaces_uses_latest_snapshots(self):
        with tempfile.TemporaryDirectory() as state_dir:
            self._write(state_dir, "tasks-2026-05-08.md", "# Old Tasks")
            self._write(state_dir, "tasks-2026-05-09.md", "# Tasks")
            self._write(state_dir, "groceries-2026-05-09.md", "# Groceries")
            self._write(state_dir, "inbox.md", "# Email")

            surfaces = {surface.key: surface for surface in discover_surfaces(state_dir)}

        self.assertTrue(surfaces["tasks"].path.endswith("tasks-2026-05-09.md"))
        self.assertTrue(surfaces["groceries"].path.endswith("groceries-2026-05-09.md"))
        self.assertTrue(surfaces["email"].path.endswith("inbox.md"))
        self.assertIsNone(surfaces["daily_brief"].path)

    def test_load_surface_reads_markdown_or_missing_message(self):
        with tempfile.TemporaryDirectory() as state_dir:
            path = self._write(state_dir, "tasks-2026-05-09.md", "# Tasks\n\n- Ship")

            content = load_surface(Surface("tasks", "Tasks", path, "markdown"), state_dir)
            missing = load_surface(Surface("finance", "Finance", None, "markdown"), state_dir)

        self.assertIn("- Ship", content)
        self.assertIn("No finance snapshot found.", missing)

    def test_load_surface_formats_errors(self):
        with tempfile.TemporaryDirectory() as state_dir:
            with open(os.path.join(state_dir, "errors.jsonl"), "w", encoding="utf-8") as f:
                f.write(json.dumps({"timestamp": "2026-05-09T10:00:00Z", "source": "x", "message": "boom"}) + "\n")

            content = load_surface(Surface("errors", "Errors", os.path.join(state_dir, "errors.jsonl"), "errors"), state_dir)

        self.assertIn("# Errors", content)
        self.assertIn("`x`: boom", content)

    def test_freshness_label(self):
        today = datetime.date(2026, 5, 9)

        self.assertEqual(freshness_label(Surface("tasks", "Tasks", "tasks-2026-05-09.md", "markdown"), today), "ok")
        self.assertEqual(freshness_label(Surface("tasks", "Tasks", "tasks-2026-05-08.md", "markdown"), today), "old")
        self.assertEqual(freshness_label(Surface("tasks", "Tasks", "tasks-2026-05-01.md", "markdown"), today), "stale")
        self.assertEqual(freshness_label(Surface("tasks", "Tasks", None, "markdown"), today), "--")

    def test_surface_row_label(self):
        label = surface_row_label(Surface("tasks", "Tasks", "tasks-2026-05-09.md", "markdown"), datetime.date(2026, 5, 9))

        self.assertEqual(label, "●  Tasks")

    def test_approvals_helpers(self):
        with tempfile.TemporaryDirectory() as state_dir:
            create_pending_action("tasks.insert", {"title": "Ship"}, "Because", "test", "ship it", state_dir)
            approvals = load_approvals(state_dir)

        rows = approval_rows(approvals)
        markdown = approval_markdown(approvals[0])

        self.assertEqual(rows[0][1], "tasks.insert")
        self.assertIn("ship it", rows[0][2])
        self.assertIn("## Args", markdown)
        self.assertIn('"title": "Ship"', markdown)

    def _write(self, state_dir: str, name: str, content: str) -> str:
        path = os.path.join(state_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path


if __name__ == "__main__":
    unittest.main()
