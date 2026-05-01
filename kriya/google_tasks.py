import datetime
import os

from kriya.daily_brief import run_gws
from kriya.utils.errors import log_error


def get_task_lists(max_results=100):
    params = {"maxResults": max_results}
    try:
        data = run_gws("tasks.tasklists.list", params)
        return data.get("items", [])
    except Exception as e:
        message = f"Error fetching task lists: {e}"
        print(message)
        log_error("tasks.tasklists", str(e), {"max_results": max_results})
        return []


def get_tasks_for_list(tasklist_id, max_results=20):
    params = {
        "tasklist": tasklist_id,
        "maxResults": max_results,
        "showCompleted": False,
        "showDeleted": False,
        "showHidden": False,
        "showAssigned": True,
    }
    try:
        data = run_gws("tasks.tasks.list", params)
        return data.get("items", [])
    except Exception as e:
        message = f"Error fetching tasks for list {tasklist_id}: {e}"
        print(message)
        log_error("tasks.tasks", str(e), {"tasklist": tasklist_id, "max_results": max_results})
        return []


def get_open_tasks(max_lists=10, max_tasks_per_list=20):
    tasks_by_list = []
    for task_list in get_task_lists(max_results=max_lists):
        tasks = get_tasks_for_list(task_list["id"], max_results=max_tasks_per_list)
        tasks_by_list.append({"list": task_list, "tasks": tasks})
    return tasks_by_list


def format_tasks(tasks_by_list, today=None):
    today = today or datetime.date.today().isoformat()
    lines = []
    total = sum(len(group["tasks"]) for group in tasks_by_list)
    if total == 0:
        return "No open tasks found.\n"

    for group in tasks_by_list:
        task_list = group["list"]
        tasks = group["tasks"]
        if not tasks:
            continue
        lines.append(f"### {task_list.get('title', 'Tasks')} ({len(tasks)})")
        for task in tasks:
            title = task.get("title", "(No Title)")
            due = task.get("due", "")
            due_label = ""
            if due:
                due_date = due.split("T")[0]
                due_label = " due today" if due_date == today else f" due {due_date}"
            lines.append(f"- **{title}**{due_label}")
            notes = task.get("notes", "")
            if notes:
                lines.append(f"  - {notes}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_tasks_snapshot(state_dir="state", today=None, max_lists=10, max_tasks_per_list=20):
    today = today or datetime.date.today().isoformat()
    os.makedirs(state_dir, exist_ok=True)
    tasks_by_list = get_open_tasks(max_lists=max_lists, max_tasks_per_list=max_tasks_per_list)
    from kriya.apple_reminders import get_reminders_by_list
    reminders = get_reminders_by_list()
    if reminders:
        tasks_by_list = tasks_by_list + reminders
    content = f"# Tasks: {today}\n\n{format_tasks(tasks_by_list, today)}"
    path = os.path.join(state_dir, f"tasks-{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Tasks snapshot written to {path}")
    return path


if __name__ == "__main__":
    write_tasks_snapshot()
