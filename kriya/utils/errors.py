import datetime
import json
import os
from typing import Any


def log_error(
    source: str,
    message: str,
    context: dict[str, Any] | None = None,
    state_dir: str = "state",
) -> None:
    os.makedirs(state_dir, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "source": source,
        "message": message,
    }
    if context is not None:
        entry["context"] = context

    with open(os.path.join(state_dir, "errors.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
