import json
import os
from typing import Any

from kriya.approvals import create_pending_action
from kriya.apple_reminders import add_reminder, complete_reminder, delete_reminder, get_reminders_for_sync, update_reminder
from kriya.google_tasks import get_tasks_for_sync
from kriya.sync import load_mappings, plan_task_sync, save_mappings
from kriya.utils.audit import log_tool_call


def run_task_sync(state_dir: str = "state", action_limit: int = 25) -> dict[str, Any]:
    google_tasks = get_tasks_for_sync()
    apple_tasks = get_reminders_for_sync() or []
    mappings = load_mappings(state_dir)
    plan = plan_task_sync(google_tasks, apple_tasks, mappings)
    actions = plan["actions"]

    if len(actions) > action_limit:
        review_path = _write_pending_plan(actions, state_dir)
        pending_path = create_pending_action(
            "sync.review",
            {"path": review_path, "action_count": len(actions)},
            "Task sync planned too many actions; inspect the plan before applying.",
            "sync:tasks",
            f"review {len(actions)} task sync actions",
            state_dir,
        )
        return {
            "aborted": True,
            "action_count": len(actions),
            "pending_review": pending_path,
            "pending_plan": review_path,
        }

    apple_results = []
    queued_paths = []
    for action in actions:
        if action["type"].endswith("_apple"):
            apple_results.append(_apply_apple_action(action, plan["mappings"]))
        elif action["type"].endswith("_google"):
            queued_paths.append(_queue_google_action(action, state_dir))

    mappings_path = save_mappings(plan["mappings"], state_dir)
    log_tool_call(
        "sync.tasks",
        {"action_count": len(actions)},
        "ok",
        {"apple_writes": len(apple_results), "queued_google_writes": len(queued_paths)},
        state_dir=state_dir,
    )
    return {
        "aborted": False,
        "action_count": len(actions),
        "apple_results": apple_results,
        "queued_google": queued_paths,
        "mappings": mappings_path,
    }


def format_task_sync_result(result: dict[str, Any]) -> str:
    if result.get("aborted"):
        return "\n".join(
            [
                f"Task sync aborted: {result['action_count']} planned actions",
                f"- review: {result['pending_plan']}",
                f"- approval: {result['pending_review']}",
            ]
        ) + "\n"
    return "\n".join(
        [
            f"Task sync complete: {result['action_count']} planned actions",
            f"- apple writes: {len(result['apple_results'])}",
            f"- queued google writes: {len(result['queued_google'])}",
            f"- mappings: {result['mappings']}",
        ]
    ) + "\n"


def _apply_apple_action(action: dict[str, Any], mappings: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    task = action.get("task", {})
    if action["type"] == "create_apple":
        uid = add_reminder("Reminders", task["title"], due=task.get("due"), notes=task.get("notes"))
        _set_mapping_apple_uid(mappings, action["google_id"], uid)
        return {"type": action["type"], "uid": uid}
    if action["type"] == "update_apple":
        if task.get("completed"):
            uid = complete_reminder(action["uid"])
        else:
            uid = update_reminder(action["uid"], title=task["title"], due=task.get("due"), notes=task.get("notes"))
        return {"type": action["type"], "uid": uid}
    if action["type"] == "delete_apple":
        uid = delete_reminder(action["uid"])
        return {"type": action["type"], "uid": uid}
    raise ValueError(f"Unsupported Apple sync action: {action['type']}")


def _queue_google_action(action: dict[str, Any], state_dir: str) -> str:
    task = action.get("task", {})
    if action["type"] == "create_google":
        tool = "tasks.insert"
        args = _google_task_args(task)
        source_id = action["apple_uid"]
    elif action["type"] == "update_google":
        tool = "tasks.update"
        args = {"id": action["id"], **_google_task_args(task)}
        source_id = action["id"]
    elif action["type"] == "delete_google":
        tool = "tasks.delete"
        args = {"id": action["id"], "tasklist": "@default"}
        source_id = action["id"]
    else:
        raise ValueError(f"Unsupported Google sync action: {action['type']}")

    return create_pending_action(
        tool,
        args,
        "Task sync requires a Google Tasks write; execute only after approval.",
        f"sync:tasks:{source_id}",
        f"{action['type']}:{task.get('title', source_id)}",
        state_dir,
    )


def _google_task_args(task: dict[str, Any]) -> dict[str, Any]:
    args = {
        "tasklist": "@default",
        "title": task.get("title", ""),
        "notes": task.get("notes", ""),
    }
    if task.get("due"):
        args["due"] = task["due"]
    if task.get("completed"):
        args["completed"] = True
    return args


def _set_mapping_apple_uid(mappings: dict[str, list[dict[str, Any]]], google_id: str, apple_uid: str) -> None:
    for row in mappings.get("tasks", []):
        if row.get("google_id") == google_id:
            row["apple_uid"] = apple_uid
            return


def _write_pending_plan(actions: list[dict[str, Any]], state_dir: str) -> str:
    path = os.path.join(state_dir, "sync", "pending-plan.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"actions": actions}, f, indent=2, sort_keys=True)
        f.write("\n")
    return path
