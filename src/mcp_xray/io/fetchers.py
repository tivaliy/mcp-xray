from pathlib import Path
from typing import Protocol

import httpx


class ContentFetcher(Protocol):
    """Protocol for fetching content from different sources."""

    def fetch(self, location: str) -> str:
        """Fetch content from the given location."""
        ...


class FileContentFetcher:
    """Fetches content from a local file."""

    def fetch(self, location: str) -> str:
        path = Path(location)
        if not path.is_file():
            msg = f"File does not exist: {location}"
            raise FileNotFoundError(msg)
        return path.read_text(encoding="utf-8")


class HttpContentFetcher:
    """Fetches content from HTTP/HTTPS URLs."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def fetch(self, location: str) -> str:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(location)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            msg = f"Failed to fetch from {location}: {e}"
            raise ConnectionError(msg) from e
