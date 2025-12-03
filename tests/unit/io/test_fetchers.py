"""Tests for mcp_xray.io.fetchers module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from mcp_xray.io.fetchers import FileContentFetcher, HttpContentFetcher


class TestFileContentFetcher:
    """Tests for FileContentFetcher class."""

    def test_fetch_existing_file(self, tmp_path: Path):
        """Test fetching content from an existing file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!", encoding="utf-8")

        fetcher = FileContentFetcher()
        content = fetcher.fetch(str(file_path))

        assert content == "Hello, World!"

    def test_fetch_json_file(self, temp_json_file: Path):
        """Test fetching JSON file content."""
        fetcher = FileContentFetcher()
        content = fetcher.fetch(str(temp_json_file))

        assert "openapi" in content
        assert "3.0.3" in content

    def test_fetch_nonexistent_file(self, tmp_path: Path):
        """Test fetching from non-existent file raises FileNotFoundError."""
        fetcher = FileContentFetcher()
        non_existent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError) as exc_info:
            fetcher.fetch(str(non_existent))

        assert "File does not exist" in str(exc_info.value)

    def test_fetch_directory_raises_error(self, tmp_path: Path):
        """Test fetching a directory raises FileNotFoundError."""
        fetcher = FileContentFetcher()

        with pytest.raises(FileNotFoundError):
            fetcher.fetch(str(tmp_path))

    def test_fetch_unicode_content(self, tmp_path: Path):
        """Test fetching file with unicode content."""
        file_path = tmp_path / "unicode.txt"
        unicode_content = "Hello, 世界! 🌍 Привет!"
        file_path.write_text(unicode_content, encoding="utf-8")

        fetcher = FileContentFetcher()
        content = fetcher.fetch(str(file_path))

        assert content == unicode_content


class TestHttpContentFetcher:
    """Tests for HttpContentFetcher class."""

    def test_default_timeout(self):
        """Test default timeout is set correctly."""
        fetcher = HttpContentFetcher()
        assert fetcher.timeout == 30.0

    def test_custom_timeout(self):
        """Test custom timeout is set correctly."""
        fetcher = HttpContentFetcher(timeout=60.0)
        assert fetcher.timeout == 60.0

    def test_fetch_successful_response(self):
        """Test successful HTTP fetch."""
        fetcher = HttpContentFetcher()

        mock_response = MagicMock()
        mock_response.text = '{"key": "value"}'
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            content = fetcher.fetch("https://example.com/api/spec.json")

            assert content == '{"key": "value"}'
            mock_client.get.assert_called_once_with("https://example.com/api/spec.json")

    def test_fetch_http_error(self):
        """Test HTTP error raises ConnectionError."""
        fetcher = HttpContentFetcher()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            mock_client_class.return_value = mock_client

            with pytest.raises(ConnectionError) as exc_info:
                fetcher.fetch("https://example.com/api/spec.json")

            assert "Failed to fetch" in str(exc_info.value)

    def test_fetch_timeout_error(self):
        """Test timeout error raises ConnectionError."""
        fetcher = HttpContentFetcher(timeout=1.0)

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value = mock_client

            with pytest.raises(ConnectionError) as exc_info:
                fetcher.fetch("https://example.com/slow")

            assert "Failed to fetch" in str(exc_info.value)

    def test_fetch_status_error(self):
        """Test HTTP status error (4xx, 5xx) raises ConnectionError."""
        fetcher = HttpContentFetcher()

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ConnectionError) as exc_info:
                fetcher.fetch("https://example.com/notfound")

            assert "Failed to fetch" in str(exc_info.value)
