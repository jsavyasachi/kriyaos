import datetime
import os
import sqlite3

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error


DEFAULT_VITALS_DB = "/Users/savya/projects/vitals/health.db"


def vitals_db() -> str:
    return os.environ.get("KRIYA_VITALS_DB", DEFAULT_VITALS_DB)


def _query_sum(con: sqlite3.Connection, record_type: str, day: str) -> float | None:
    row = con.execute(
        "select sum(value) from records where type = ? and date = ?",
        (record_type, day),
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def _query_avg(con: sqlite3.Connection, record_type: str, day: str) -> float | None:
    row = con.execute(
        "select avg(value) from records where type = ? and date = ?",
        (record_type, day),
    ).fetchone()
    return row[0] if row and row[0] is not None else None


def _latest_workout(con: sqlite3.Connection) -> dict | None:
    row = con.execute(
        """
        select activity_type, duration, duration_unit, total_energy_kcal,
               total_distance, distance_unit, start_date
        from workouts
        order by start_date desc
        limit 1
        """
    ).fetchone()
    if not row:
        return None
    return {
        "activity_type": row[0],
        "duration": row[1],
        "duration_unit": row[2],
        "total_energy_kcal": row[3],
        "total_distance": row[4],
        "distance_unit": row[5],
        "start_date": row[6],
    }


def get_vitals_summary(
    db_path: str | None = None,
    today: str | None = None,
    state_dir: str = "state",
) -> dict:
    today = today or datetime.date.today().isoformat()
    db_path = db_path or vitals_db()
    yesterday = (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat()
    if not os.path.exists(db_path):
        log_error("vitals", "health.db not found", {"path": db_path}, state_dir)
        return {}

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        summary = {
            "date": today,
            "sleep_hours": _query_sum(con, "HKCategoryTypeIdentifierSleepAnalysis", yesterday),
            "steps": _query_sum(con, "HKQuantityTypeIdentifierStepCount", today),
            "resting_hr": _query_avg(con, "HKQuantityTypeIdentifierRestingHeartRate", today),
            "last_workout": _latest_workout(con),
        }
        log_tool_call("vitals.read", {"date": today}, "ok", {"fields": len(summary)}, state_dir=state_dir)
        return summary
    except sqlite3.Error as e:
        log_error("vitals", "health.db read failed", {"error": str(e)}, state_dir)
        log_tool_call("vitals.read", {"date": today}, "error", error=str(e), state_dir=state_dir)
        return {}
    finally:
        con.close()


def _format_number(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "unavailable"
    if digits == 0:
        return f"{value:,.0f}"
    return f"{value:,.{digits}f}"


def format_vitals(summary: dict, today: str | None = None) -> str:
    today = today or summary.get("date") or datetime.date.today().isoformat()
    if not summary:
        return f"# Vitals {today}\n\n_unavailable_\n"

    sleep_hours = summary.get("sleep_hours")
    resting_hr = summary.get("resting_hr")
    sleep_label = f"{_format_number(sleep_hours, 1)} hours" if sleep_hours is not None else "unavailable"
    resting_label = f"{_format_number(resting_hr)} bpm" if resting_hr is not None else "unavailable"
    lines = [
        f"# Vitals {today}",
        "",
        f"- Sleep: {sleep_label}",
        f"- Steps: {_format_number(summary.get('steps'))}",
        f"- Resting HR: {resting_label}",
    ]
    workout = summary.get("last_workout")
    if workout:
        duration = _format_number(workout.get("duration"), 1)
        duration_unit = workout.get("duration_unit") or "min"
        energy = _format_number(workout.get("total_energy_kcal"))
        lines.append(
            f"- Last workout: {workout.get('activity_type', 'workout')} "
            f"({duration} {duration_unit}, {energy} kcal, {workout.get('start_date', 'unknown date')})"
        )
    else:
        lines.append("- Last workout: unavailable")
    return "\n".join(lines) + "\n"


def format_vitals_section(summary: dict) -> str:
    return format_vitals(summary).split("\n", 2)[2] if summary else "Vitals unavailable.\n"


def write_vitals_snapshot(
    state_dir: str = "state",
    today: str | None = None,
    db_path: str | None = None,
) -> str:
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)
    summary = get_vitals_summary(db_path=db_path, today=today, state_dir=state_dir)
    path = os.path.join(state_dir, f"vitals-{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(format_vitals(summary, today))
    print(f"Vitals snapshot written to {path}")
    return path
