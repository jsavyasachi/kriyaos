import json
import os
import tempfile
import unittest

from kriya.inbox import latest_matching_file, render_inbox


class TestInbox(unittest.TestCase):
    def test_latest_matching_file(self):
        with tempfile.TemporaryDirectory() as state_dir:
            open(os.path.join(state_dir, "tasks-2026-04-29.md"), "w").close()
            open(os.path.join(state_dir, "tasks-2026-04-30.md"), "w").close()

            latest = latest_matching_file(state_dir, "tasks-")

        self.assertTrue(latest.endswith("tasks-2026-04-30.md"))

    def test_render_inbox(self):
        with tempfile.TemporaryDirectory() as state_dir:
            with open(os.path.join(state_dir, "tasks-2026-04-30.md"), "w", encoding="utf-8") as f:
                f.write("# Tasks\n\n- Ship")
            with open(os.path.join(state_dir, "inbox.md"), "w", encoding="utf-8") as f:
                f.write("## Email Triage\n\n- Hello")
            with open(os.path.join(state_dir, "errors.jsonl"), "w", encoding="utf-8") as f:
                f.write(json.dumps({"timestamp": "2026-04-30T01:00:00Z", "source": "x", "message": "boom"}) + "\n")

            content = render_inbox(state_dir)

        self.assertIn("# Kriya Inbox", content)
        self.assertIn("## Pending Approvals", content)
        self.assertIn("- Ship", content)
        self.assertIn("`x`: boom", content)
