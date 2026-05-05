import os
import tempfile
import unittest
from unittest.mock import patch

from kriya.approvals import approve_action, create_pending_action, reject_action
from kriya.execute import execute_action


def _make_approved_action(state_dir, tool="calendar.create_event", args=None):
    args = args or {
        "summary": "Dentist",
        "start": "2026-05-01T10:00:00",
        "end": "2026-05-01T11:00:00",
    }
    create_pending_action(tool, args, "book appointment", "email", "dentist appt", state_dir=state_dir)
    items = [
        f for f in os.listdir(os.path.join(state_dir, "pending")) if f.endswith(".json")
    ]
    approval_id = items[0].replace(".json", "")
    approve_action(approval_id, state_dir)
    return approval_id


class TestExecuteAction(unittest.TestCase):
    @patch("kriya.execute._TOOLS", {"calendar.create_event": lambda args: {"id": "evt123"}})
    def test_executes_approved_action(self):
        with tempfile.TemporaryDirectory() as state_dir:
            approval_id = _make_approved_action(state_dir)
            item = execute_action(approval_id, state_dir)

        self.assertEqual(item["status"], "executed")
        self.assertIn("executed_at", item)
        self.assertEqual(item["result"], {"id": "evt123"})

    @patch("kriya.execute._TOOLS", {"calendar.create_event": lambda args: {"id": "evt123"}})
    def test_idempotent_on_double_execute(self):
        with tempfile.TemporaryDirectory() as state_dir:
            approval_id = _make_approved_action(state_dir)
            execute_action(approval_id, state_dir)
            item = execute_action(approval_id, state_dir)  # second call

        self.assertEqual(item["status"], "executed")

    def test_raises_on_pending_status(self):
        with tempfile.TemporaryDirectory() as state_dir:
            args = {"summary": "X", "start": "2026-05-01T10:00:00", "end": "2026-05-01T11:00:00"}
            create_pending_action("calendar.create_event", args, "r", "s", "i", state_dir=state_dir)
            items = os.listdir(os.path.join(state_dir, "pending"))
            approval_id = items[0].replace(".json", "")

            with self.assertRaises(ValueError):
                execute_action(approval_id, state_dir)

    def test_raises_on_unknown_tool(self):
        with tempfile.TemporaryDirectory() as state_dir:
            args = {"summary": "X", "start": "2026-05-01T10:00:00", "end": "2026-05-01T11:00:00"}
            create_pending_action("unknown.tool", args, "r", "s", "i", state_dir=state_dir)
            items = os.listdir(os.path.join(state_dir, "pending"))
            approval_id = items[0].replace(".json", "")
            approve_action(approval_id, state_dir)

            with self.assertRaises(ValueError):
                execute_action(approval_id, state_dir)

    def test_raises_on_missing_action(self):
        with tempfile.TemporaryDirectory() as state_dir:
            with self.assertRaises(FileNotFoundError):
                execute_action("doesnotexist", state_dir)


class TestCreateCalendarEvent(unittest.TestCase):
    @patch("kriya.execute._TOOLS", {})
    @patch("kriya.daily_brief.run_gws")
    def test_passes_correct_params_to_gws(self, mock_gws):
        mock_gws.return_value = {"id": "evt123", "status": "confirmed"}
        from kriya.execute import _create_calendar_event
        _create_calendar_event({
            "summary": "Dentist",
            "start": "2026-05-01T10:00:00",
            "end": "2026-05-01T11:00:00",
            "description": "Annual checkup",
        })
        call_args = mock_gws.call_args
        self.assertEqual(call_args[0][0], "calendar.events.insert")
        params = call_args[0][1]
        self.assertEqual(params["summary"], "Dentist")
        self.assertEqual(params["start"]["dateTime"], "2026-05-01T10:00:00")
        self.assertEqual(params["description"], "Annual checkup")


class TestInsertTask(unittest.TestCase):
    @patch("kriya.daily_brief.run_gws")
    def test_passes_correct_params_to_gws(self, mock_gws):
        mock_gws.return_value = {"id": "task123", "status": "needsAction"}
        from kriya.execute import _insert_task
        _insert_task({"tasklist": "@default", "title": "Follow up", "notes": "Check this"})
        call_args = mock_gws.call_args
        self.assertEqual(call_args[0][0], "tasks.tasks.insert")
        params = call_args[0][1]
        self.assertEqual(params["title"], "Follow up")
        self.assertEqual(params["notes"], "Check this")


class TestApproveReject(unittest.TestCase):
    def test_approve_sets_status(self):
        with tempfile.TemporaryDirectory() as state_dir:
            args = {"summary": "X", "start": "2026-05-01T10:00:00", "end": "2026-05-01T11:00:00"}
            create_pending_action("calendar.create_event", args, "r", "s", "i", state_dir=state_dir)
            items = os.listdir(os.path.join(state_dir, "pending"))
            approval_id = items[0].replace(".json", "")

            item = approve_action(approval_id, state_dir)

        self.assertEqual(item["status"], "approved")
        self.assertIn("approved_at", item)

    def test_reject_sets_status(self):
        with tempfile.TemporaryDirectory() as state_dir:
            args = {"summary": "X", "start": "2026-05-01T10:00:00", "end": "2026-05-01T11:00:00"}
            create_pending_action("calendar.create_event", args, "r", "s", "i", state_dir=state_dir)
            items = os.listdir(os.path.join(state_dir, "pending"))
            approval_id = items[0].replace(".json", "")

            item = reject_action(approval_id, state_dir)

        self.assertEqual(item["status"], "rejected")
        self.assertIn("rejected_at", item)
