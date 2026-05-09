import contextlib
import io
import tempfile
import unittest
from unittest.mock import patch

from kriya.groceries import format_groceries, get_groceries, write_groceries_snapshot


class TestGroceries(unittest.TestCase):
    def test_get_groceries_reads_apple_groceries_list(self):
        with patch("kriya.groceries.get_reminders_for_list", return_value=[{"title": "Milk"}]) as mock_get:
            self.assertEqual(get_groceries(), [{"title": "Milk"}])

        mock_get.assert_called_once_with("Groceries")

    def test_format_groceries_handles_empty(self):
        self.assertEqual(format_groceries([]), "No groceries found.\n")

    def test_format_groceries_marks_completion(self):
        content = format_groceries([
            {"title": "Milk", "completed": False},
            {"title": "Eggs", "completed": True},
        ])

        self.assertIn("- [ ] Milk", content)
        self.assertIn("- [x] Eggs", content)

    @patch("kriya.groceries.get_groceries", return_value=[{"title": "Milk", "completed": False}])
    def test_write_groceries_snapshot(self, _mock_get):
        with tempfile.TemporaryDirectory() as state_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                path = write_groceries_snapshot(state_dir=state_dir, today="2026-05-09")

            with open(path, encoding="utf-8") as f:
                content = f.read()

        self.assertTrue(path.endswith("groceries-2026-05-09.md"))
        self.assertIn("# Groceries: 2026-05-09", content)
        self.assertIn("- [ ] Milk", content)


if __name__ == "__main__":
    unittest.main()
