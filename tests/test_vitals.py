import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from kriya.vitals import format_vitals, format_vitals_section, get_vitals_summary, write_vitals_snapshot


def create_vitals_db(path):
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            create table records (
                id integer primary key autoincrement,
                type text not null,
                value real not null,
                unit text,
                start_date text not null,
                end_date text not null,
                source_name text,
                date text generated always as (substr(start_date, 1, 10)) stored
            );
            create table workouts (
                id integer primary key autoincrement,
                activity_type text not null,
                duration real,
                duration_unit text,
                total_energy_kcal real,
                total_distance real,
                distance_unit text,
                start_date text not null,
                end_date text not null,
                source_name text,
                date text generated always as (substr(start_date, 1, 10)) stored
            );
            """
        )
        con.executemany(
            """
            insert into records (type, value, unit, start_date, end_date, source_name)
            values (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "HKCategoryTypeIdentifierSleepAnalysis",
                    7.5,
                    "hr",
                    "2026-05-04 23:00:00 -0700",
                    "2026-05-05 06:30:00 -0700",
                    "Apple Watch",
                ),
                (
                    "HKQuantityTypeIdentifierStepCount",
                    1200,
                    "count",
                    "2026-05-05 08:00:00 -0700",
                    "2026-05-05 09:00:00 -0700",
                    "Apple Watch",
                ),
                (
                    "HKQuantityTypeIdentifierStepCount",
                    800,
                    "count",
                    "2026-05-05 10:00:00 -0700",
                    "2026-05-05 11:00:00 -0700",
                    "Apple Watch",
                ),
                (
                    "HKQuantityTypeIdentifierRestingHeartRate",
                    58,
                    "count/min",
                    "2026-05-05 07:00:00 -0700",
                    "2026-05-05 07:01:00 -0700",
                    "Apple Watch",
                ),
                (
                    "HKQuantityTypeIdentifierRestingHeartRate",
                    62,
                    "count/min",
                    "2026-05-05 12:00:00 -0700",
                    "2026-05-05 12:01:00 -0700",
                    "Apple Watch",
                ),
            ],
        )
        con.execute(
            """
            insert into workouts (
                activity_type, duration, duration_unit, total_energy_kcal,
                total_distance, distance_unit, start_date, end_date, source_name
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "HKWorkoutActivityTypeYoga",
                30,
                "min",
                120,
                0,
                None,
                "2026-05-05 18:00:00 -0700",
                "2026-05-05 18:30:00 -0700",
                "Apple Watch",
            ),
        )
        con.commit()
    finally:
        con.close()


class TestVitals(unittest.TestCase):
    def test_get_vitals_summary_reads_sqlite(self):
        with tempfile.TemporaryDirectory() as state_dir:
            db_path = os.path.join(state_dir, "health.db")
            create_vitals_db(db_path)

            summary = get_vitals_summary(db_path=db_path, today="2026-05-05", state_dir=state_dir)

        self.assertEqual(summary["sleep_hours"], 7.5)
        self.assertEqual(summary["steps"], 2000)
        self.assertEqual(summary["resting_hr"], 60)
        self.assertEqual(summary["last_workout"]["activity_type"], "HKWorkoutActivityTypeYoga")

    @patch("kriya.vitals.get_vitals_summary")
    def test_write_vitals_snapshot(self, mock_summary):
        mock_summary.return_value = {
            "date": "2026-05-05",
            "sleep_hours": 7.5,
            "steps": 2000,
            "resting_hr": 60,
            "last_workout": None,
        }

        with tempfile.TemporaryDirectory() as state_dir:
            path = write_vitals_snapshot(state_dir=state_dir, today="2026-05-05", db_path="ignored.db")

            with open(path, encoding="utf-8") as f:
                contents = f.read()

        self.assertTrue(path.endswith("vitals-2026-05-05.md"))
        self.assertIn("# Vitals 2026-05-05", contents)
        self.assertIn("- Sleep: 7.5 hours", contents)
        self.assertIn("- Steps: 2,000", contents)
        mock_summary.assert_called_once_with(db_path="ignored.db", today="2026-05-05", state_dir=state_dir)

    def test_format_vitals_handles_empty(self):
        self.assertEqual(format_vitals({}, "2026-05-05"), "# Vitals 2026-05-05\n\n_unavailable_\n")
        self.assertEqual(format_vitals_section({}), "Vitals unavailable.\n")
