import datetime
import json
import os
from typing import Any


def log_tool_call(
    tool: str,
    args: dict[str, Any],
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    state_dir: str = "state",
) -> None:
    os.makedirs(state_dir, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "tool": tool,
        "args": args,
        "status": status,
    }
    if result is not None:
        entry["result"] = result
    if error is not None:
        entry["error"] = error

    with open(os.path.join(state_dir, "audit.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
