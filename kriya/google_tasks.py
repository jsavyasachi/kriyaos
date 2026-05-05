import datetime
import os
from typing import Any

from kriya.daily_brief import run_gws
from kriya.execute import register
from kriya.utils.errors import log_error


def get_task_lists(max_results=100):
    params = {"maxResults": max_results}
    try:
        data = run_gws("tasks.tasklists.list", params)
        return data.get("items", [])
    except Exception as e:
        log_error("tasks.tasklists", str(e), {"max_results": max_results})
        raise


def get_tasks_for_list(tasklist_id, max_results=20, show_completed=False, show_deleted=False):
    params = {
        "tasklist": tasklist_id,
        "maxResults": max_results,
        "showCompleted": show_completed,
        "showDeleted": show_deleted,
        "showHidden": False,
        "showAssigned": True,
    }
    try:
        data = run_gws("tasks.tasks.list", params)
        return data.get("items", [])
    except Exception as e:
        log_error("tasks.tasks", str(e), {"tasklist": tasklist_id, "max_results": max_results})
        raise


def get_open_tasks(max_lists=10, max_tasks_per_list=20):
    tasks_by_list = []
    for task_list in get_task_lists(max_results=max_lists):
        tasks = get_tasks_for_list(task_list["id"], max_results=max_tasks_per_list)
        tasks_by_list.append({"list": task_list, "tasks": tasks})
    return tasks_by_list


def get_tasks_for_sync(max_lists=10, max_tasks_per_list=100):
    tasks = []
    for task_list in get_task_lists(max_results=max_lists):
        tasklist_id = task_list["id"]
        for task in get_tasks_for_list(
            tasklist_id,
            max_results=max_tasks_per_list,
            show_completed=True,
            show_deleted=True,
        ):
            tasks.append(normalize_task_for_sync(task, tasklist_id))
    return tasks


def normalize_task_for_sync(task: dict[str, Any], tasklist_id: str = "@default") -> dict[str, Any]:
    due = task.get("due")
    return {
        "id": task.get("id"),
        "tasklist": tasklist_id,
        "title": task.get("title", ""),
        "due": due.split("T")[0] if due else None,
        "notes": task.get("notes", ""),
        "completed": task.get("status") == "completed",
        "deleted": bool(task.get("deleted", False)),
        "updated": task.get("updated"),
    }


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


@register("tasks.insert")
def insert_task(args: dict) -> dict:
    params = {
        "tasklist": args.get("tasklist", "@default"),
        "title": args["title"],
    }
    if args.get("notes"):
        params["notes"] = args["notes"]
    if args.get("due"):
        params["due"] = args["due"]
    return run_gws("tasks.tasks.insert", params)


@register("tasks.update")
def update_task(args: dict[str, Any]) -> dict:
    params = {
        "tasklist": args.get("tasklist", "@default"),
        "task": args["id"],
    }
    params.update(_task_patch(args))
    return run_gws("tasks.tasks.patch", params)


@register("tasks.complete")
def complete_task(args: dict[str, Any]) -> dict:
    completed_at = args.get("completed") or datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    params = {
        "tasklist": args.get("tasklist", "@default"),
        "task": args["id"],
        "status": "completed",
        "completed": completed_at,
    }
    return run_gws("tasks.tasks.patch", params)


@register("tasks.delete")
def delete_task(args: dict[str, Any]) -> dict:
    return run_gws(
        "tasks.tasks.delete",
        {
            "tasklist": args.get("tasklist", "@default"),
            "task": args["id"],
        },
    )


def _task_patch(args: dict[str, Any]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for field in ("title", "notes", "due"):
        if field in args:
            patch[field] = args[field]
    if "completed" in args:
        if args["completed"]:
            patch["status"] = "completed"
            patch["completed"] = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
        else:
            patch["status"] = "needsAction"
    if "status" in args:
        patch["status"] = args["status"]
    return patch


if __name__ == "__main__":
    write_tasks_snapshot()
