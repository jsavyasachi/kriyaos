import copy
import datetime
import hashlib
import json
import os
from typing import Any


def empty_mappings() -> dict[str, list[dict[str, Any]]]:
    return {"tasks": [], "events": []}


def mappings_path(state_dir: str = "state") -> str:
    return os.path.join(state_dir, "sync", "mappings.json")


def load_mappings(state_dir: str = "state") -> dict[str, list[dict[str, Any]]]:
    path = mappings_path(state_dir)
    if not os.path.exists(path):
        return empty_mappings()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {"tasks": data.get("tasks", []), "events": data.get("events", [])}


def save_mappings(mappings: dict[str, list[dict[str, Any]]], state_dir: str = "state") -> str:
    path = mappings_path(state_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def title_hash(title: str, due: str | None = None) -> str:
    value = f"{title.strip().lower()}:{due or ''}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def plan_task_sync(
    google_tasks: list[dict[str, Any]],
    apple_tasks: list[dict[str, Any]],
    mappings: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    current = copy.deepcopy(mappings or empty_mappings())
    rows = current.setdefault("tasks", [])
    current.setdefault("events", [])
    actions: list[dict[str, Any]] = []
    matched_google: set[str] = set()
    matched_apple: set[str] = set()

    google_by_id = {task["id"]: task for task in google_tasks if task.get("id")}
    apple_by_uid = {task["uid"]: task for task in apple_tasks if task.get("uid")}

    for row in list(rows):
        google = google_by_id.get(row.get("google_id"))
        apple = apple_by_uid.get(row.get("apple_uid"))
        if google:
            matched_google.add(google["id"])
        if apple:
            matched_apple.add(apple["uid"])
        _plan_mapped_pair(row, google, apple, actions)

    for google in google_tasks:
        google_id = google.get("id")
        if not google_id or google_id in matched_google:
            continue
        apple = _find_bootstrap_match(google, apple_tasks, matched_apple)
        row = _new_task_mapping(google=google, apple=apple)
        rows.append(row)
        matched_google.add(google_id)
        if apple:
            matched_apple.add(apple["uid"])
            _plan_mapped_pair(row, google, apple, actions)
        elif not google.get("deleted"):
            actions.append({"type": "create_apple", "source": "google", "task": _task_payload(google)})

    for apple in apple_tasks:
        apple_uid = apple.get("uid")
        if not apple_uid or apple_uid in matched_apple:
            continue
        row = _new_task_mapping(google=None, apple=apple)
        rows.append(row)
        matched_apple.add(apple_uid)
        if not apple.get("deleted"):
            actions.append({"type": "create_google", "source": "apple", "task": _task_payload(apple)})

    return {"actions": actions, "mappings": current}


def _plan_mapped_pair(
    row: dict[str, Any],
    google: dict[str, Any] | None,
    apple: dict[str, Any] | None,
    actions: list[dict[str, Any]],
) -> None:
    if google and apple:
        _refresh_mapping(row, google, apple)
        if google.get("deleted") and not apple.get("deleted"):
            actions.append({"type": "delete_apple", "source": "google", "uid": apple["uid"]})
            return
        if apple.get("deleted") and not google.get("deleted"):
            actions.append({"type": "delete_google", "source": "apple", "id": google["id"]})
            return
        if google.get("deleted") and apple.get("deleted"):
            return
        if _task_payload(google) == _task_payload(apple):
            return
        winner = _winner_source(google, apple, row)
        if winner == "google":
            actions.append({"type": "update_apple", "source": "google", "uid": apple["uid"], "task": _task_payload(google)})
        else:
            actions.append({"type": "update_google", "source": "apple", "id": google["id"], "task": _task_payload(apple)})
        row["last_modified_at_source"] = winner
        row["last_modified_ts"] = _updated_at(google if winner == "google" else apple)
        return

    if google and not google.get("deleted"):
        row["last_seen_google"] = _updated_at(google)
        actions.append({"type": "create_apple", "source": "google", "task": _task_payload(google)})
    if apple and not apple.get("deleted"):
        row["last_seen_apple"] = _updated_at(apple)
        actions.append({"type": "create_google", "source": "apple", "task": _task_payload(apple)})


def _find_bootstrap_match(
    google: dict[str, Any],
    apple_tasks: list[dict[str, Any]],
    matched_apple: set[str],
) -> dict[str, Any] | None:
    for apple in apple_tasks:
        apple_uid = apple.get("uid")
        if not apple_uid or apple_uid in matched_apple:
            continue
        if _task_key(google) == _task_key(apple):
            return apple
    return None


def _new_task_mapping(
    google: dict[str, Any] | None,
    apple: dict[str, Any] | None,
) -> dict[str, Any]:
    source_task = google or apple or {}
    winner = "google" if google else "apple"
    return {
        "google_id": google.get("id") if google else None,
        "apple_uid": apple.get("uid") if apple else None,
        "title_hash": _task_key(source_task),
        "last_seen_google": _updated_at(google),
        "last_seen_apple": _updated_at(apple),
        "last_modified_at_source": winner,
        "last_modified_ts": _updated_at(source_task),
    }


def _refresh_mapping(row: dict[str, Any], google: dict[str, Any], apple: dict[str, Any]) -> None:
    row["google_id"] = google.get("id")
    row["apple_uid"] = apple.get("uid")
    row["title_hash"] = _task_key(google)
    row["last_seen_google"] = _updated_at(google)
    row["last_seen_apple"] = _updated_at(apple)


def _task_key(task: dict[str, Any]) -> str:
    return title_hash(task.get("title", ""), task.get("due"))


def _task_payload(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": task.get("title", ""),
        "due": task.get("due"),
        "notes": task.get("notes", ""),
        "completed": bool(task.get("completed", False)),
    }


def _winner_source(google: dict[str, Any], apple: dict[str, Any], row: dict[str, Any]) -> str:
    google_ts = _parse_time(_updated_at(google))
    apple_ts = _parse_time(_updated_at(apple))
    if google_ts and apple_ts:
        return "google" if google_ts >= apple_ts else "apple"
    return row.get("last_modified_at_source") or "google"


def _updated_at(task: dict[str, Any] | None) -> str | None:
    if not task:
        return None
    return task.get("updated_at") or task.get("updated") or task.get("modified") or task.get("last_modified")


def _parse_time(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
