import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os

# Add parent directory to path so we can import kriya
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kriya.utils.secrets import get_secret

class TestGetSecret(unittest.TestCase):
    @patch('kriya.utils.secrets.subprocess.run')
    def test_get_secret_success(self, mock_run):
        # Mock a successful op CLI execution
        mock_result = MagicMock()
        mock_result.stdout = " my_super_secret_value \n"
        mock_run.return_value = mock_result

        result = get_secret("test_item", "password")
        
        self.assertEqual(result, "my_super_secret_value")
        mock_run.assert_called_once_with(
            ["op", "item", "get", "test_item", "--fields", "password", "--reveal"],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('kriya.utils.secrets.subprocess.run')
    @patch('kriya.utils.secrets.sys.exit')
    def test_get_secret_failure(self, mock_exit, mock_run):
        # Mock a failed op CLI execution (e.g., item not found)
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, 
            cmd=["op", "item", "get", "bad_item"], 
            stderr="Item not found"
        )
        
        get_secret("bad_item", "password")
        
        # Verify it gracefully exits the script with status 1
        mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
