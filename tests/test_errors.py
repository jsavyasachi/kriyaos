import tempfile
import unittest

from kriya.utils.errors import log_error, read_recent_errors


class TestErrors(unittest.TestCase):
    def test_read_recent_errors_returns_tail(self):
        with tempfile.TemporaryDirectory() as state_dir:
            log_error("one", "first", state_dir=state_dir)
            log_error("two", "second", state_dir=state_dir)
            log_error("three", "third", state_dir=state_dir)

            errors = read_recent_errors(state_dir, limit=2)

        self.assertEqual([error["source"] for error in errors], ["two", "three"])

    def test_read_recent_errors_missing_file(self):
        with tempfile.TemporaryDirectory() as state_dir:
            errors = read_recent_errors(state_dir)

        self.assertEqual(errors, [])
