import contextlib
import io
import tempfile
import unittest
from unittest.mock import patch

from kriya.google_keep import (
    format_notes,
    get_grocery_items,
    get_notes,
    get_notes_section,
    normalize_keep_list_items,
    replace_note,
    write_notes_snapshot,
)


class TestGoogleKeep(unittest.TestCase):
    def test_format_notes_handles_empty(self):
        self.assertEqual(format_notes([]), "No notes found.\n")

    def test_format_notes_handles_text_body(self):
        content = format_notes(
            [
                {
                    "title": "Ideas",
                    "updateTime": "2026-05-05T10:00:00Z",
                    "body": {"text": {"text": "Build the thing"}},
                }
            ]
        )

        self.assertIn("- **Ideas** updated 2026-05-05", content)
        self.assertIn("  - Build the thing", content)

    def test_format_notes_handles_list_body(self):
        content = format_notes(
            [
                {
                    "title": "Groceries",
                    "body": {
                        "list": {
                            "listItems": [
                                {"text": {"text": "Milk"}, "checked": False},
                                {"text": {"text": "Coffee"}, "checked": True},
                            ]
                        }
                    },
                }
            ]
        )

        self.assertIn("  - [ ] Milk", content)
        self.assertIn("  - [x] Coffee", content)

    @patch("kriya.google_keep.run_gws", return_value={"notes": [{"title": "Ideas"}]})
    def test_get_notes_uses_keep_notes_list(self, mock_gws):
        self.assertEqual(get_notes(page_size=3), [{"title": "Ideas"}])
        mock_gws.assert_called_once_with("keep.notes.list", {"pageSize": 3})

    def test_normalize_keep_list_items(self):
        items = normalize_keep_list_items(
            {
                "updateTime": "2026-05-09T10:00:00Z",
                "body": {
                    "list": {
                        "listItems": [
                            {"name": "items/1", "text": {"text": "Milk"}, "checked": False},
                            {"name": "items/2", "text": {"text": "Eggs"}, "checked": True},
                        ]
                    }
                },
            }
        )

        self.assertEqual(items[0], {"id": "items/1", "title": "Milk", "completed": False, "updated": "2026-05-09T10:00:00Z"})
        self.assertEqual(items[1]["completed"], True)

    @patch("kriya.google_keep.run_gws")
    def test_get_grocery_items_fetches_matching_note(self, mock_gws):
        mock_gws.side_effect = [
            {"notes": [{"name": "notes/1", "title": "Groceries"}]},
            {
                "name": "notes/1",
                "title": "Groceries",
                "updateTime": "2026-05-09T10:00:00Z",
                "body": {"list": {"listItems": [{"text": {"text": "Milk"}}]}},
            },
        ]

        groceries = get_grocery_items()

        self.assertEqual(groceries["name"], "notes/1")
        self.assertEqual(groceries["items"][0]["title"], "Milk")

    @patch("kriya.google_keep.run_gws")
    def test_replace_note_deletes_then_creates(self, mock_gws):
        mock_gws.side_effect = [{}, {"name": "notes/new"}]

        result = replace_note({"name": "notes/old", "title": "Groceries", "items": [{"title": "Milk"}]})

        self.assertEqual(result, {"name": "notes/new"})
        self.assertEqual(mock_gws.call_args_list[0].args, ("keep.notes.delete", {"name": "notes/old"}))
        self.assertEqual(mock_gws.call_args_list[1].args[0], "keep.notes.create")

    @patch("kriya.google_keep.run_gws", side_effect=RuntimeError("missing scope"))
    def test_get_notes_section_omits_on_missing_scope(self, _gws):
        with tempfile.TemporaryDirectory() as state_dir:
            self.assertIsNone(get_notes_section(state_dir=state_dir))

    @patch("kriya.google_keep.get_notes_section", return_value="- **Ideas**\n")
    def test_write_notes_snapshot(self, mock_section):
        with tempfile.TemporaryDirectory() as state_dir:
            with contextlib.redirect_stdout(io.StringIO()):
                path = write_notes_snapshot(state_dir=state_dir, today="2026-05-05")

            with open(path, encoding="utf-8") as f:
                contents = f.read()

        self.assertTrue(path.endswith("notes-2026-05-05.md"))
        self.assertIn("# Notes: 2026-05-05", contents)
        self.assertIn("- **Ideas**", contents)
        mock_section.assert_called_once_with(page_size=20, state_dir=state_dir)
