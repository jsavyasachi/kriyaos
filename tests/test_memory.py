import unittest
from unittest.mock import MagicMock, patch


class TestMemory(unittest.TestCase):
    def _mock_client(self):
        client = MagicMock()
        client.search.return_value = {
            "results": [
                {"memory": "Prefers morning meetings", "score": 0.9},
                {"memory": "Dislikes status emails", "score": 0.7},
            ]
        }
        client.get_all.return_value = {
            "results": [
                {"id": "1", "memory": "Prefers morning meetings"},
                {"id": "2", "memory": "Dislikes status emails"},
            ]
        }
        return client

    @patch("kriya.memory.get_client")
    def test_add_calls_client(self, mock_get_client):
        mock_get_client.return_value = self._mock_client()
        from kriya.memory import add
        result = add("I prefer morning meetings")
        self.assertTrue(result)
        mock_get_client.return_value.add.assert_called_once()

    @patch("kriya.memory.get_client")
    def test_search_returns_strings(self, mock_get_client):
        mock_get_client.return_value = self._mock_client()
        from kriya.memory import search
        results = search("meeting preferences")
        self.assertEqual(results, ["Prefers morning meetings", "Dislikes status emails"])

    @patch("kriya.memory.get_client")
    def test_get_all_returns_list(self, mock_get_client):
        mock_get_client.return_value = self._mock_client()
        from kriya.memory import get_all
        results = get_all()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["memory"], "Prefers morning meetings")

    @patch("kriya.memory.get_client", side_effect=RuntimeError("no client"))
    def test_add_returns_false_when_init_fails(self, _):
        from kriya.memory import add
        self.assertFalse(add("anything"))

    @patch("kriya.memory.get_client", side_effect=RuntimeError("no client"))
    def test_search_returns_empty_when_init_fails(self, _):
        from kriya.memory import search
        self.assertEqual(search("anything"), [])

    @patch("kriya.memory.get_client", side_effect=RuntimeError("no client"))
    def test_get_all_returns_empty_when_init_fails(self, _):
        from kriya.memory import get_all
        self.assertEqual(get_all(), [])

    @patch("kriya.memory.log_error")
    @patch("kriya.memory._ollama_reachable", return_value=True)
    def test_get_client_raises_on_init_failure(self, _reach, _log_error):
        import kriya.memory as memory

        memory._client = None
        memory._init_failed = False
        with patch.dict("sys.modules", {"mem0": None}):
            with self.assertRaises(ModuleNotFoundError):
                memory.get_client()
        memory._init_failed = False

    @patch("kriya.memory._ollama_reachable", return_value=False)
    def test_get_client_returns_none_when_ollama_unreachable(self, _reach):
        import kriya.memory as memory

        memory._client = None
        memory._init_failed = False
        self.assertIsNone(memory.get_client())
        memory._init_failed = False


class TestFormatMemories(unittest.TestCase):
    def test_format_returns_none_for_empty(self):
        from kriya.memory import format_memories
        self.assertIsNone(format_memories([]))

    def test_format_returns_bullet_list(self):
        from kriya.memory import format_memories
        result = format_memories(["Prefers mornings", "Dislikes status emails"])
        self.assertIn("- Prefers mornings", result)
        self.assertIn("- Dislikes status emails", result)
