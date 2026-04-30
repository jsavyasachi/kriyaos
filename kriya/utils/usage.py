import datetime
import json
import os
from typing import Any


DEFAULT_DAILY_LIMIT_USD = 2.0


def parse_daily_limit(value: str | None) -> float:
    if value is None or value == "":
        return DEFAULT_DAILY_LIMIT_USD
    return float(value)


def usage_path(state_dir: str = "state") -> str:
    return os.path.join(state_dir, "usage.jsonl")


def log_usage(
    source: str,
    cost_usd: float,
    metadata: dict[str, Any] | None = None,
    state_dir: str = "state",
) -> None:
    os.makedirs(state_dir, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "source": source,
        "cost_usd": cost_usd,
    }
    if metadata is not None:
        entry["metadata"] = metadata

    with open(usage_path(state_dir), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def daily_spend_usd(day: str, state_dir: str = "state") -> float:
    path = usage_path(state_dir)
    if not os.path.exists(path):
        return 0.0

    total = 0.0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("timestamp", "").startswith(day):
                total += float(entry.get("cost_usd", 0.0))
    return total


def cost_ceiling_reached(day: str, state_dir: str = "state", limit_usd: float | None = None) -> bool:
    limit = DEFAULT_DAILY_LIMIT_USD if limit_usd is None else limit_usd
    return daily_spend_usd(day, state_dir) >= limit
