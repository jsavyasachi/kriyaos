import json
import os
from typing import Any

from kriya.approvals import create_pending_action
from kriya.apple_reminders import add_reminder, complete_reminder, get_reminders_for_list
from kriya.google_keep import get_grocery_items
from kriya.sync_routes import get_sync_route
from kriya.utils.audit import log_tool_call

GROCERY_ROUTE = get_sync_route("groceries")


def run_grocery_sync(state_dir: str = "state", action_limit: int = 25) -> dict[str, Any]:
    google_list = get_grocery_items(GROCERY_ROUTE["google"]["note"], state_dir=state_dir)
    if google_list is None:
        raise RuntimeError("Google Keep Groceries note was not found or Keep auth is unavailable")

    apple_items = get_reminders_for_list(GROCERY_ROUTE["apple"]["list"]) or []
    actions = plan_grocery_sync(google_list, apple_items)

    if len(actions) > action_limit:
        review_path = _write_pending_plan(actions, state_dir)
        pending_path = create_pending_action(
            "sync.review",
            {"path": review_path, "action_count": len(actions)},
            "Grocery sync planned too many actions; inspect the plan before applying.",
            "sync:groceries",
            f"review {len(actions)} grocery sync actions",
            state_dir,
        )
        return {
            "aborted": True,
            "action_count": len(actions),
            "pending_review": pending_path,
            "pending_plan": review_path,
        }

    apple_results = []
    queued_google = []
    for action in actions:
        if action["type"].endswith("_apple"):
            apple_results.append(_apply_apple_action(action))
        elif action["type"] == "replace_google":
            queued_google.append(_queue_google_replace(action, google_list, apple_items, state_dir))

    log_tool_call(
        "sync.groceries",
        {"action_count": len(actions)},
        "ok",
        {"apple_writes": len(apple_results), "queued_google_writes": len(queued_google)},
        state_dir=state_dir,
    )
    return {
        "aborted": False,
        "action_count": len(actions),
        "apple_results": apple_results,
        "queued_google": queued_google,
    }


def plan_grocery_sync(google_list: dict[str, Any], apple_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    google_items = google_list.get("items", [])
    google_by_key = {_item_key(item): item for item in google_items}
    apple_by_key = {_item_key(item): item for item in apple_items}
    needs_google_replace = False

    for key, google in google_by_key.items():
        apple = apple_by_key.get(key)
        if apple is None:
            if not google.get("completed"):
                actions.append({"type": "create_apple", "source": "google", "item": _item_payload(google)})
            continue
        if bool(google.get("completed", False)) != bool(apple.get("completed", False)):
            if _google_wins(google, apple):
                if google.get("completed"):
                    actions.append({"type": "complete_apple", "source": "google", "uid": apple["uid"]})
            else:
                needs_google_replace = True

    for key, apple in apple_by_key.items():
        if key not in google_by_key:
            needs_google_replace = True

    if needs_google_replace:
        actions.append({"type": "replace_google", "source": "apple"})
    return actions


def format_grocery_sync_result(result: dict[str, Any]) -> str:
    if result.get("aborted"):
        return "\n".join(
            [
                f"Grocery sync aborted: {result['action_count']} planned actions",
                f"- review: {result['pending_plan']}",
                f"- approval: {result['pending_review']}",
            ]
        ) + "\n"
    return "\n".join(
        [
            f"Grocery sync complete: {result['action_count']} planned actions",
            f"- apple writes: {len(result['apple_results'])}",
            f"- queued google writes: {len(result['queued_google'])}",
        ]
    ) + "\n"


def _apply_apple_action(action: dict[str, Any]) -> dict[str, Any]:
    if action["type"] == "create_apple":
        item = action["item"]
        uid = add_reminder(GROCERY_ROUTE["apple"]["list"], item["title"])
        return {"type": action["type"], "uid": uid}
    if action["type"] == "complete_apple":
        uid = complete_reminder(action["uid"])
        return {"type": action["type"], "uid": uid}
    raise ValueError(f"Unsupported Apple grocery action: {action['type']}")


def _queue_google_replace(
    action: dict[str, Any],
    google_list: dict[str, Any],
    apple_items: list[dict[str, Any]],
    state_dir: str,
) -> str:
    items = [_item_payload(item) for item in apple_items if not item.get("deleted")]
    return create_pending_action(
        "keep.replace_note",
        {"name": google_list.get("name"), "title": google_list.get("title", "Groceries"), "items": items},
        "Grocery sync requires replacing the Google Keep Groceries note; execute only after approval.",
        "sync:groceries",
        f"{action['type']}:{google_list.get('name', 'Groceries')}",
        state_dir,
    )


def _write_pending_plan(actions: list[dict[str, Any]], state_dir: str) -> str:
    path = os.path.join(state_dir, "sync", "pending-grocery-plan.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"actions": actions}, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def _item_key(item: dict[str, Any]) -> str:
    return item.get("title", "").strip().lower()


def _item_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {"title": item.get("title", ""), "completed": bool(item.get("completed", False))}


def _google_wins(google: dict[str, Any], apple: dict[str, Any]) -> bool:
    google_updated = google.get("updated")
    apple_updated = apple.get("updated")
    if not google_updated or not apple_updated:
        return True
    return google_updated >= apple_updated
