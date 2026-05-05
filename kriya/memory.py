import os

from kriya.utils.audit import log_tool_call
from kriya.utils.errors import log_error

USER_ID = "savya"
_client = None


def _mem0_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "state", "mem0"))


def get_client():
    global _client
    if _client is not None:
        return _client
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
        raise


def add(text: str, metadata: dict = None) -> bool:
    client = get_client()
    try:
        client.add(text, user_id=USER_ID, metadata=metadata or {})
        log_tool_call("memory.add", {"text": text[:100]}, "ok", {})
        return True
    except Exception as e:
        log_error("memory.add", str(e), {"text": text[:100]})
        raise


def search(query: str, limit: int = 5) -> list[str]:
    client = get_client()
    try:
        results = client.search(query, user_id=USER_ID, limit=limit)
        memories = [r["memory"] for r in results.get("results", [])]
        log_tool_call("memory.search", {"query": query}, "ok", {"count": len(memories)})
        return memories
    except Exception as e:
        log_error("memory.search", str(e), {"query": query})
        raise


def format_memories(memories: list[str]) -> str | None:
    if not memories:
        return None
    return "\n".join(f"- {m}" for m in memories) + "\n"


def get_all() -> list[dict]:
    client = get_client()
    try:
        results = client.get_all(user_id=USER_ID)
        return results.get("results", [])
    except Exception as e:
        log_error("memory.get_all", str(e), {})
        raise
