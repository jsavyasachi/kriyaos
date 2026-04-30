import subprocess
import json
import sys

def get_secret(item_name: str, field: str = "credential") -> str:
    """
    Fetches a secret from 1Password using the `op` CLI.
    Assumes `op` is installed and authenticated (Touch ID).
    """
    try:
        result = subprocess.run(
            ["op", "item", "get", item_name, "--fields", field, "--reveal"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching secret '{item_name}' (field: {field}) from 1Password.", file=sys.stderr)
        print(f"op CLI error: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
