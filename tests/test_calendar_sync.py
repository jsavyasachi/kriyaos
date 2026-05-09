import unittest

from kriya.sync import event_key, plan_event_sync


def google_event(**overrides):
    event = {
        "id": "g1",
        "title": "Doctor",
        "start": "2026-05-10T09:00:00-07:00",
        "end": "2026-05-10T09:30:00-07:00",
        "all_day": False,
        "description": "Annual checkup",
        "location": "Clinic",
        "updated": "2026-05-05T10:00:00Z",
    }
    event.update(overrides)
    return event


def apple_event(**overrides):
    event = {
        "uid": "a1",
        "title": "Doctor",
        "start": "2026-05-10T09:00:00-07:00",
        "end": "2026-05-10T09:30:00-07:00",
        "all_day": False,
        "description": "Annual checkup",
        "location": "Clinic",
        "updated": "2026-05-05T10:00:00Z",
    }
    event.update(overrides)
    return event


def event_mapping(**overrides):
    mapping = {
        "google_id": "g1",
        "apple_uid": "a1",
        "event_key": event_key("Doctor", "2026-05-10T09:00:00-07:00"),
        "last_seen_google": "2026-05-05T10:00:00Z",
        "last_seen_apple": "2026-05-05T10:00:00Z",
        "last_modified_at_source": "google",
        "last_modified_ts": "2026-05-05T10:00:00Z",
    }
    mapping.update(overrides)
    return mapping


class TestEventSyncPlanner(unittest.TestCase):
    def test_bootstrap_exact_title_and_start_creates_mapping_without_action(self):
        result = plan_event_sync([google_event()], [apple_event()], {"tasks": [], "events": []})

        self.assertEqual(result["actions"], [])
        self.assertEqual(result["mappings"]["events"][0]["google_id"], "g1")
        self.assertEqual(result["mappings"]["events"][0]["apple_uid"], "a1")

    def test_google_only_event_creates_apple_action(self):
        result = plan_event_sync([google_event()], [], {"tasks": [], "events": []})

        self.assertEqual(result["actions"][0]["type"], "create_apple")
        self.assertEqual(result["actions"][0]["event"]["title"], "Doctor")

    def test_apple_only_event_creates_google_action(self):
        result = plan_event_sync([], [apple_event()], {"tasks": [], "events": []})

        self.assertEqual(result["actions"][0]["type"], "create_google")
        self.assertEqual(result["actions"][0]["event"]["title"], "Doctor")

    def test_newer_google_title_edit_wins(self):
        result = plan_event_sync(
            [google_event(title="Dentist", updated="2026-05-05T11:00:00Z")],
            [apple_event(updated="2026-05-05T10:00:00Z")],
            {"tasks": [], "events": [event_mapping()]},
        )

        self.assertEqual(result["actions"][0]["type"], "update_apple")
        self.assertEqual(result["actions"][0]["event"]["title"], "Dentist")

    def test_newer_apple_time_edit_wins(self):
        result = plan_event_sync(
            [google_event(updated="2026-05-05T10:00:00Z")],
            [apple_event(start="2026-05-10T10:00:00-07:00", updated="2026-05-05T11:00:00Z")],
            {"tasks": [], "events": [event_mapping()]},
        )

        self.assertEqual(result["actions"][0]["type"], "update_google")
        self.assertEqual(result["actions"][0]["event"]["start"], "2026-05-10T10:00:00-07:00")

    def test_explicit_google_delete_deletes_apple(self):
        result = plan_event_sync(
            [google_event(deleted=True)],
            [apple_event()],
            {"tasks": [], "events": [event_mapping()]},
        )

        self.assertEqual(result["actions"], [{"type": "delete_apple", "source": "google", "apple_uid": "a1"}])

    def test_explicit_apple_delete_deletes_google(self):
        result = plan_event_sync(
            [google_event()],
            [apple_event(deleted=True)],
            {"tasks": [], "events": [event_mapping()]},
        )

        self.assertEqual(result["actions"], [{"type": "delete_google", "source": "apple", "google_id": "g1"}])

    def test_all_day_payload_differs_from_timed_event(self):
        result = plan_event_sync(
            [google_event(start="2026-05-10", end="2026-05-11", all_day=True, updated="2026-05-05T11:00:00Z")],
            [apple_event(updated="2026-05-05T10:00:00Z")],
            {"tasks": [], "events": [event_mapping()]},
        )

        self.assertEqual(result["actions"][0]["type"], "update_apple")
        self.assertTrue(result["actions"][0]["event"]["all_day"])


if __name__ == "__main__":
    unittest.main()
