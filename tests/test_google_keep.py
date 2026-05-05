import contextlib
import io
import tempfile
import unittest
from unittest.mock import patch

from kriya.google_keep import format_notes, get_notes, get_notes_section, write_notes_snapshot


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
