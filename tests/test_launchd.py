import plistlib
import unittest
from pathlib import Path


class TestLaunchdTemplate(unittest.TestCase):
    def test_daily_brief_template_is_valid_plist(self):
        template = Path("launchd/com.savyasachi.kriyaos.daily-brief.plist.template")
        data = plistlib.loads(template.read_bytes())

        self.assertEqual(data["Label"], "com.savyasachi.kriyaos.daily-brief")
        self.assertEqual(data["StartCalendarInterval"], {"Hour": 7, "Minute": 0})
        self.assertFalse(data["RunAtLoad"])
        self.assertEqual(data["ProgramArguments"][1:], ["-m", "kriya", "daily-brief"])
