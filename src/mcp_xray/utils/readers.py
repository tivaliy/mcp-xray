import json
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx
import yaml
from pydantic import BaseModel

# Type aliases
type Extension = str
type Scheme = str


class ContentFetcher(Protocol):
    """Protocol for fetching content from different sources."""

    def fetch(self, location: str) -> str:
        """Fetch content from the given location."""
        ...


class ContentReader(Protocol):
    """Protocol for reading content in different formats."""

    def read_content(self, content: str) -> dict[str, Any]:
        """Parse content string into a dictionary."""
        ...


class DataValidator(Protocol):
    """Protocol for validating loaded data."""

    def validate(self, data: dict[str, Any]) -> Any:
        """Validate and potentially transform the data."""
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


class JsonReader:
    """Reader for JSON content."""

    def read_content(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON content: {e}"
            raise ValueError(msg) from e


class YamlReader:
    """Reader for YAML content."""

    def read_content(self, content: str) -> dict[str, Any]:
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            msg = f"Invalid YAML content: {e}"
            raise ValueError(msg) from e


class NoOpValidator:
    """Validator that returns data unchanged."""

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        return data


class PydanticValidator:
    """Validator for Pydantic BaseModel classes."""

    def __init__(self, model_class: type[BaseModel]) -> None:
        self.model_class = model_class

    def validate(self, data: dict[str, Any]) -> BaseModel:
        try:
            return self.model_class.model_validate(data)
        except Exception as e:
            msg = f"Pydantic validation failed: {e}"
            raise ValueError(msg) from e


class DataReaderError(Exception):
    """Base exception for DataReader errors."""


class UnsupportedSchemeError(DataReaderError):
    """Raised when an unsupported URL scheme is encountered."""


class UnsupportedExtensionError(DataReaderError):
    """Raised when an unsupported file extension is encountered."""


class DataReader:
    """Manages different readers and fetchers for data files."""

    DEFAULT_SCHEMA: Scheme = "file"

    def __init__(self, default_validator: DataValidator | None = None) -> None:
        self._reader_classes: dict[Extension, type[ContentReader]] = {
            ".json": JsonReader,
            ".yaml": YamlReader,
            ".yml": YamlReader,
        }

        self._fetcher_classes: dict[Scheme, type[ContentFetcher]] = {
            "file": FileContentFetcher,
            "http": HttpContentFetcher,
            "https": HttpContentFetcher,
        }

        self._default_validator = default_validator or NoOpValidator()

    def register_reader(self, extension: Extension, reader_class: type[ContentReader]) -> None:
        """Register a new content reader class for a file extension."""
        self._reader_classes[extension.lower()] = reader_class

    def register_fetcher(self, scheme: Scheme, fetcher_class: type[ContentFetcher]) -> None:
        """Register a new content fetcher class for a URL scheme."""
        self._fetcher_classes[scheme.lower()] = fetcher_class

    def _create_fetcher(self, scheme: Scheme) -> ContentFetcher:
        """Create a fetcher instance for the given scheme."""
        fetcher_class = self._fetcher_classes.get(scheme)
        if not fetcher_class:
            msg = f"No fetcher registered for scheme: {scheme}"
            raise UnsupportedSchemeError(msg)
        return fetcher_class()

    def _create_reader(self, extension: Extension) -> ContentReader:
        """Create a reader instance for the given extension."""
        reader_class = self._reader_classes.get(extension)
        if not reader_class:
            msg = f"No reader registered for extension: {extension}"
            raise UnsupportedExtensionError(msg)
        return reader_class()

    def load_from(self, file_location: str, *, validator: DataValidator | None = None) -> Any:
        """
        Load data from a file location (local path or URL).

        Args:
            file_location: Path to local file or URL

        Returns:
            Parsed data as a dictionary

        Raises:
            UnsupportedSchemeError: If the URL scheme is not supported
            UnsupportedExtensionError: If the file extension is not supported
            FileNotFoundError: If the local file doesn't exist
            ConnectionError: If fetching from URL fails
            ValueError: If the content cannot be parsed
        """
        parsed = urlparse(file_location)
        scheme = parsed.scheme if parsed.scheme else self.DEFAULT_SCHEMA

        # Handle both URL paths and local file paths
        path = parsed.path if parsed.scheme else file_location
        extension = Path(path).suffix.lower()

        # Create instances only when needed
        fetcher = self._create_fetcher(scheme)
        reader = self._create_reader(extension)

        content = fetcher.fetch(file_location)
        data = reader.read_content(content)

        # Use provided validator or default
        active_validator = validator or self._default_validator
        return active_validator.validate(data)
