import asyncio
import importlib.util
import os
import tempfile
import unittest
from unittest.mock import patch

from kriya.approvals import create_pending_action, pending_path

if importlib.util.find_spec("textual") is None:
    raise unittest.SkipTest("Textual is not installed")

from kriya.tui.app import KriyaApp, RefreshState


class TestTuiApp(unittest.IsolatedAsyncioTestCase):
    async def test_mount_loads_surfaces_and_approvals(self):
        with tempfile.TemporaryDirectory() as state_dir:
            self._write(state_dir, "tasks-2026-05-09.md", "# Tasks\n\n- Ship")
            create_pending_action("tasks.insert", {"title": "Ship"}, "Because", "test", "ship", state_dir)

            app = KriyaApp(state_dir=state_dir, watch=False)
            async with app.run_test() as pilot:
                await pilot.pause()

                self.assertTrue(any(surface.key == "tasks" for surface in app.surfaces))
                self.assertEqual(len(app.approvals), 1)

    async def test_approve_key_updates_pending_file(self):
        with tempfile.TemporaryDirectory() as state_dir:
            approval_id = create_pending_action("tasks.insert", {"title": "Ship"}, "Because", "test", "ship", state_dir)

            app = KriyaApp(state_dir=state_dir, watch=False)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#approval-table").focus()
                await pilot.press("a")
                await pilot.pause()

            item = self._read_pending(state_dir, self._approval_id_from_path(approval_id))

        self.assertEqual(item["status"], "approved")

    async def test_reject_key_updates_pending_file(self):
        with tempfile.TemporaryDirectory() as state_dir:
            approval_path = create_pending_action("tasks.insert", {"title": "Ship"}, "Because", "test", "ship", state_dir)

            app = KriyaApp(state_dir=state_dir, watch=False)
            async with app.run_test() as pilot:
                await pilot.pause()
                app.query_one("#approval-table").focus()
                await pilot.press("r")
                await pilot.pause()

            item = self._read_pending(state_dir, self._approval_id_from_path(approval_path))

        self.assertEqual(item["status"], "rejected")

    async def test_poll_key_runs_worker(self):
        poll_result = {
            "date": "2026-05-09",
            "tasks": "state/tasks.md",
            "notes": "state/notes.md",
            "groceries": "state/groceries.md",
            "finance": "state/finance.md",
            "vitals": "state/vitals.md",
            "email_triage": "state/inbox.md",
            "daily_brief": "state/daily.md",
        }
        with tempfile.TemporaryDirectory() as state_dir:
            app = KriyaApp(state_dir=state_dir, watch=False)
            with patch("kriya.tui.app.run_poll", return_value=poll_result) as mock_poll:
                async with app.run_test() as pilot:
                    await pilot.press("p")
                    await self._wait_until(lambda: mock_poll.called)

        mock_poll.assert_called_once_with(state_dir=state_dir)

    async def test_refresh_message_reloads_surfaces(self):
        with tempfile.TemporaryDirectory() as state_dir:
            app = KriyaApp(state_dir=state_dir, watch=False)
            async with app.run_test() as pilot:
                await pilot.pause()
                self._write(state_dir, "finance-2026-05-09.md", "# Finance")
                app.post_message(RefreshState())
                await pilot.pause()

                finance = next(surface for surface in app.surfaces if surface.key == "finance")

        self.assertTrue(finance.path.endswith("finance-2026-05-09.md"))

    async def _wait_until(self, predicate, timeout: float = 2.0) -> None:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            if predicate():
                return
            await asyncio.sleep(0.05)
        self.fail("condition was not met before timeout")

    def _write(self, state_dir: str, name: str, content: str) -> str:
        path = os.path.join(state_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _read_pending(self, state_dir: str, approval_id: str) -> dict:
        import json

        with open(pending_path(state_dir, approval_id), encoding="utf-8") as f:
            return json.load(f)

    def _approval_id_from_path(self, path: str) -> str:
        return os.path.basename(path).removesuffix(".json")


if __name__ == "__main__":
    unittest.main()
