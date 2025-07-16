import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


def load_json(file_location: str) -> dict[str, Any]:
    """Loads file of JSON format from a local file path or remote URL.

    Args:
        file_path: Path to a local file or URL to a remote JSON file

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        FileNotFoundError: If local file doesn't exist
        httpx.HTTPError: If remote URL cannot be fetched
        json.JSONDecodeError: If the content is not valid JSON
    """
    # Check if it's a URL
    parsed = urlparse(file_location)
    if parsed.scheme in ("http", "https"):
        # Load from remote URL
        with httpx.Client() as client:
            response = client.get(file_location)
            response.raise_for_status()
            return response.json()
    else:
        # Load from local file
        path = Path(file_location)
        if not path.is_file():
            msg = f"OpenAPI spec file does not exist: {file_location}"
            raise FileNotFoundError(msg)

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
