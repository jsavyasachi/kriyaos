import json
import os
import tempfile
import unittest

from kriya.sync import load_mappings, plan_task_sync, save_mappings, title_hash


def google_task(**overrides):
    task = {
        "id": "g1",
        "title": "File taxes",
        "due": "2026-05-10",
        "notes": "Use official report",
        "completed": False,
        "updated": "2026-05-05T10:00:00Z",
    }
    task.update(overrides)
    return task


def apple_task(**overrides):
    task = {
        "uid": "a1",
        "title": "File taxes",
        "due": "2026-05-10",
        "notes": "Use official report",
        "completed": False,
        "updated": "2026-05-05T10:00:00Z",
    }
    task.update(overrides)
    return task


def task_mapping(**overrides):
    mapping = {
        "google_id": "g1",
        "apple_uid": "a1",
        "title_hash": title_hash("File taxes", "2026-05-10"),
        "last_seen_google": "2026-05-05T10:00:00Z",
        "last_seen_apple": "2026-05-05T10:00:00Z",
        "last_modified_at_source": "google",
        "last_modified_ts": "2026-05-05T10:00:00Z",
    }
    mapping.update(overrides)
    return mapping


class TestTaskSyncPlanner(unittest.TestCase):
    def test_bootstrap_exact_title_and_due_creates_mapping_without_action(self):
        result = plan_task_sync([google_task()], [apple_task()], {"tasks": [], "events": []})

        self.assertEqual(result["actions"], [])
        self.assertEqual(result["mappings"]["tasks"][0]["google_id"], "g1")
        self.assertEqual(result["mappings"]["tasks"][0]["apple_uid"], "a1")

    def test_google_only_task_creates_apple_action(self):
        result = plan_task_sync([google_task()], [], {"tasks": [], "events": []})

        self.assertEqual(result["actions"][0]["type"], "create_apple")
        self.assertEqual(result["actions"][0]["task"]["title"], "File taxes")

    def test_apple_only_task_creates_google_action(self):
        result = plan_task_sync([], [apple_task()], {"tasks": [], "events": []})

        self.assertEqual(result["actions"][0]["type"], "create_google")
        self.assertEqual(result["actions"][0]["task"]["title"], "File taxes")

    def test_newer_google_update_wins(self):
        result = plan_task_sync(
            [google_task(title="File taxes today", updated="2026-05-05T11:00:00Z")],
            [apple_task(updated="2026-05-05T10:00:00Z")],
            {"tasks": [task_mapping()], "events": []},
        )

        self.assertEqual(result["actions"][0]["type"], "update_apple")
        self.assertEqual(result["actions"][0]["task"]["title"], "File taxes today")

    def test_newer_apple_completion_wins(self):
        result = plan_task_sync(
            [google_task(updated="2026-05-05T10:00:00Z")],
            [apple_task(completed=True, updated="2026-05-05T11:00:00Z")],
            {"tasks": [task_mapping()], "events": []},
        )

        self.assertEqual(result["actions"][0]["type"], "update_google")
        self.assertTrue(result["actions"][0]["task"]["completed"])

    def test_explicit_google_delete_deletes_apple(self):
        result = plan_task_sync(
            [google_task(deleted=True)],
            [apple_task()],
            {"tasks": [task_mapping()], "events": []},
        )

        self.assertEqual(result["actions"], [{"type": "delete_apple", "source": "google", "uid": "a1"}])

    def test_explicit_apple_delete_deletes_google(self):
        result = plan_task_sync(
            [google_task()],
            [apple_task(deleted=True)],
            {"tasks": [task_mapping()], "events": []},
        )

        self.assertEqual(result["actions"], [{"type": "delete_google", "source": "apple", "id": "g1"}])


class TestMappingsPersistence(unittest.TestCase):
    def test_load_missing_mappings_returns_empty_shape(self):
        with tempfile.TemporaryDirectory() as state_dir:
            self.assertEqual(load_mappings(state_dir), {"tasks": [], "events": []})

    def test_save_and_load_mappings(self):
        mappings = {"tasks": [task_mapping()], "events": []}
        with tempfile.TemporaryDirectory() as state_dir:
            path = save_mappings(mappings, state_dir)
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            loaded = load_mappings(state_dir)

        self.assertTrue(path.endswith(os.path.join("sync", "mappings.json")))
        self.assertEqual(raw, mappings)
        self.assertEqual(loaded, mappings)
