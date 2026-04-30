import os
import tempfile
import unittest

from kriya.utils.usage import cost_ceiling_reached, daily_spend_usd, log_usage, parse_daily_limit


class TestUsage(unittest.TestCase):
    def test_parse_daily_limit_defaults_to_two_dollars(self):
        self.assertEqual(parse_daily_limit(None), 2.0)
        self.assertEqual(parse_daily_limit(""), 2.0)
        self.assertEqual(parse_daily_limit("3.50"), 3.5)

    def test_daily_spend_sums_matching_day(self):
        with tempfile.TemporaryDirectory() as state_dir:
            usage = os.path.join(state_dir, "usage.jsonl")
            with open(usage, "w", encoding="utf-8") as f:
                f.write('{"timestamp":"2026-04-30T01:00:00Z","cost_usd":0.75}\n')
                f.write('{"timestamp":"2026-04-30T02:00:00Z","cost_usd":1.25}\n')
                f.write('{"timestamp":"2026-05-01T01:00:00Z","cost_usd":5.00}\n')

            self.assertEqual(daily_spend_usd("2026-04-30", state_dir), 2.0)
            self.assertTrue(cost_ceiling_reached("2026-04-30", state_dir, 2.0))
            self.assertFalse(cost_ceiling_reached("2026-04-30", state_dir, 2.01))

    def test_log_usage_appends_entry(self):
        with tempfile.TemporaryDirectory() as state_dir:
            log_usage("daily_brief", 0.0, {"reason": "read-only"}, state_dir)

            with open(os.path.join(state_dir, "usage.jsonl"), encoding="utf-8") as f:
                contents = f.read()

        self.assertIn('"source": "daily_brief"', contents)
        self.assertIn('"cost_usd": 0.0', contents)
