import os
import socket
import urllib.parse

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error

USER_ID = "savya"
OLLAMA_BASE_URL = "http://localhost:11434"
_client = None
_init_failed = False


def _mem0_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "state", "mem0"))


def _ollama_reachable(base_url: str = OLLAMA_BASE_URL, timeout: float = 0.25) -> bool:
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 11434
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def get_client():
    global _client, _init_failed
    if _client is not None:
        return _client
    if _init_failed:
        return None
    if not _ollama_reachable():
        _init_failed = True
        return None
    try:
        from mem0 import Memory
        os.makedirs(_mem0_dir(), exist_ok=True)
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {"path": _mem0_dir()},
            },
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": "qwen2.5:7b",
                    "ollama_base_url": "http://localhost:11434",
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {"model": "multi-qa-MiniLM-L6-cos-v1"},
            },
        }
        _client = Memory.from_config(config)
        return _client
    except Exception as e:
        log_error("memory.init", str(e), {})
        _init_failed = True
        raise


def _safe_client():
    try:
        return get_client()
    except Exception:
        return None


def add(text: str, metadata: dict = None) -> bool:
    client = _safe_client()
    if client is None:
        return False
    try:
        client.add(text, user_id=USER_ID, metadata=metadata or {})
        log_tool_call("memory.add", {"text": text[:100]}, "ok", {})
        return True
    except Exception as e:
        log_error("memory.add", str(e), {"text": text[:100]})
        return False


def search(query: str, limit: int = 5) -> list[str]:
    client = _safe_client()
    if client is None:
        return []
    try:
        results = client.search(query, user_id=USER_ID, limit=limit)
        memories = [r["memory"] for r in results.get("results", [])]
        log_tool_call("memory.search", {"query": query}, "ok", {"count": len(memories)})
        return memories
    except Exception as e:
        log_error("memory.search", str(e), {"query": query})
        return []


def format_memories(memories: list[str]) -> str | None:
    if not memories:
        return None
    return "\n".join(f"- {m}" for m in memories) + "\n"


def get_all() -> list[dict]:
    client = _safe_client()
    if client is None:
        return []
    try:
        results = client.get_all(user_id=USER_ID)
        return results.get("results", [])
    except Exception as e:
        log_error("memory.get_all", str(e), {})
        return []
