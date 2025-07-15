import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


def load_openapi_spec(spec_location: str) -> dict[str, Any]:
    """Load the OpenAPI spec from a local file path or remote URL.

    Args:
        spec_location: Path to a local file or URL to a remote OpenAPI spec

    Returns:
        Dictionary containing the parsed OpenAPI specification

    Raises:
        FileNotFoundError: If local file doesn't exist
        httpx.HTTPError: If remote URL cannot be fetched
        json.JSONDecodeError: If the content is not valid JSON
    """
    # Check if it's a URL
    parsed = urlparse(spec_location)
    if parsed.scheme in ("http", "https"):
        # Load from remote URL
        with httpx.Client() as client:
            response = client.get(spec_location)
            response.raise_for_status()
            return response.json()
    else:
        # Load from local file
        path = Path(spec_location)
        if not path.is_file():
            msg = f"OpenAPI spec file does not exist: {spec_location}"
            raise FileNotFoundError(msg)

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
