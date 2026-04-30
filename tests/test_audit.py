import json
import os
import tempfile
import unittest

from kriya.utils.audit import log_tool_call


class TestAuditLog(unittest.TestCase):
    def test_log_tool_call_writes_jsonl_entry(self):
        with tempfile.TemporaryDirectory() as state_dir:
            log_tool_call(
                "gws.calendar.events.list",
                {"calendarId": "primary"},
                "ok",
                {"count": 2},
                state_dir=state_dir,
            )

            audit_path = os.path.join(state_dir, "audit.jsonl")
            with open(audit_path, encoding="utf-8") as f:
                entry = json.loads(f.readline())

        self.assertEqual(entry["tool"], "gws.calendar.events.list")
        self.assertEqual(entry["args"], {"calendarId": "primary"})
        self.assertEqual(entry["status"], "ok")
        self.assertEqual(entry["result"], {"count": 2})
        self.assertIn("timestamp", entry)
