import datetime
import hashlib
import json
import os
from typing import Any


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def make_idempotency_key(tool: str, source: str, intent: str) -> str:
    return stable_hash(f"{tool}:{source}:{intent}")


def pending_dir(state_dir: str = "state") -> str:
    return os.path.join(state_dir, "pending")


def pending_path(state_dir: str, approval_id: str) -> str:
    return os.path.join(pending_dir(state_dir), f"{approval_id}.json")


def create_pending_action(
    tool: str,
    args: dict[str, Any],
    rationale: str,
    source: str,
    intent: str,
    state_dir: str = "state",
    expires_days: int = 7,
) -> str:
    idempotency_key = make_idempotency_key(tool, source, intent)
    approval_id = stable_hash(idempotency_key)
    path = pending_path(state_dir, approval_id)
    if os.path.exists(path):
        return path

    now = datetime.datetime.now(datetime.UTC)
    item = {
        "id": approval_id,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + datetime.timedelta(days=expires_days)).isoformat().replace("+00:00", "Z"),
        "status": "pending",
        "tool": tool,
        "args": args,
        "rationale": rationale,
        "source": source,
        "intent": intent,
        "idempotency_key": idempotency_key,
    }

    os.makedirs(pending_dir(state_dir), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def list_pending_actions(state_dir: str = "state") -> list[dict[str, Any]]:
    directory = pending_dir(state_dir)
    if not os.path.exists(directory):
        return []

    items = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as f:
            item = json.load(f)
        if item.get("status") == "pending":
            items.append(item)
    return items


def _update_status(approval_id: str, status: str, state_dir: str = "state", **extra) -> dict:
    path = pending_path(state_dir, approval_id)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No pending action found: {approval_id}")
    with open(path, encoding="utf-8") as f:
        item = json.load(f)
    item["status"] = status
    item.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, sort_keys=True)
        f.write("\n")
    return item


def approve_action(approval_id: str, state_dir: str = "state") -> dict:
    now = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    return _update_status(approval_id, "approved", state_dir, approved_at=now)


def reject_action(approval_id: str, state_dir: str = "state") -> dict:
    now = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    return _update_status(approval_id, "rejected", state_dir, rejected_at=now)


def format_pending_actions(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No pending actions.\n"

    lines = []
    for item in items:
        lines.append(f"- **{item['id']}** `{item['tool']}`: {item['intent']}")
        lines.append(f"  - {item['rationale']}")
    return "\n".join(lines) + "\n"
