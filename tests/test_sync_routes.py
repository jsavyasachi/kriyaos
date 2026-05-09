import unittest

from kriya.sync_routes import get_sync_route


class TestSyncRoutes(unittest.TestCase):
    def test_task_route_maps_google_tasks_to_apple_todo(self):
        route = get_sync_route("tasks.todo")

        self.assertEqual(route["google"], {"service": "tasks", "list": "To Do"})
        self.assertEqual(route["apple"], {"service": "reminders", "list": "To do"})

    def test_groceries_route_is_apple_only(self):
        route = get_sync_route("groceries")

        self.assertEqual(route["apple"], {"service": "reminders", "list": "Groceries"})
        self.assertEqual(route["mode"], "apple_only")

    def test_reminders_route_is_apple_only(self):
        route = get_sync_route("reminders")

        self.assertEqual(route["apple"], {"service": "reminders", "list": "Reminders"})
        self.assertEqual(route["mode"], "apple_only")

    def test_unknown_route_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_sync_route("calendar.primary")


if __name__ == "__main__":
    unittest.main()
