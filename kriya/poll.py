import datetime

from kriya.daily_brief import generate_daily_brief
from kriya.email_triage import append_email_triage
from kriya.google_tasks import write_tasks_snapshot


def run_poll(state_dir="state", today=None, force=False):
    today = today or datetime.date.today().isoformat()
    results = {
        "date": today,
        "tasks": write_tasks_snapshot(state_dir=state_dir, today=today),
        "email_triage": append_email_triage(state_dir=state_dir, today=today, force=force),
        "daily_brief": generate_daily_brief(state_dir=state_dir, today=today, force=force),
    }
    return results


def format_poll_result(results):
    return "\n".join(
        [
            f"Poll complete: {results['date']}",
            f"- tasks: {results['tasks']}",
            f"- email_triage: {results['email_triage']}",
            f"- daily_brief: {results['daily_brief']}",
        ]
    ) + "\n"


if __name__ == "__main__":
    print(format_poll_result(run_poll()), end="")
