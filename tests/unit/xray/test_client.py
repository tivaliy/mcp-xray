"""Tests for mcp_xray.xray.client module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_xray.core.config import AppSettings
from mcp_xray.xray.client import XrayClient


class TestXrayClient:
    """Tests for XrayClient class."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock AppSettings for testing."""
        settings = MagicMock(spec=AppSettings)
        settings.url = "https://xray.example.com"
        settings.auth_type = "pat"
        settings.personal_token = "test-token-12345"
        settings.timeout = 20.0
        return settings

    def test_from_config_creates_client(self, mock_settings):
        """Test from_config creates XrayClient with correct configuration."""
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_client_instance = MagicMock()
            mock_async_client.return_value = mock_client_instance

            client = XrayClient.from_config(mock_settings)

            assert isinstance(client, XrayClient)
            mock_async_client.assert_called_once()

    def test_from_config_sets_base_url(self, mock_settings):
        """Test from_config sets correct base URL."""
        with patch("httpx.AsyncClient") as mock_async_client:
            XrayClient.from_config(mock_settings)

            call_kwargs = mock_async_client.call_args.kwargs
            assert call_kwargs["base_url"] == "https://xray.example.com"

    def test_from_config_sets_authorization_header(self, mock_settings):
        """Test from_config sets correct Authorization header."""
        with patch("httpx.AsyncClient") as mock_async_client:
            XrayClient.from_config(mock_settings)

            call_kwargs = mock_async_client.call_args.kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "Bearer test-token-12345"

    def test_from_config_sets_content_type_header(self, mock_settings):
        """Test from_config sets Content-Type header."""
        with patch("httpx.AsyncClient") as mock_async_client:
            XrayClient.from_config(mock_settings)

            call_kwargs = mock_async_client.call_args.kwargs
            assert "Content-Type" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Content-Type"] == "application/json"

    def test_from_config_sets_timeout(self, mock_settings):
        """Test from_config sets correct timeout."""
        mock_settings.timeout = 30.0

        with patch("httpx.AsyncClient") as mock_async_client:
            XrayClient.from_config(mock_settings)

            call_kwargs = mock_async_client.call_args.kwargs
            assert isinstance(call_kwargs["timeout"], httpx.Timeout)

    def test_from_config_missing_token_raises_error(self, mock_settings):
        """Test from_config raises error when token is missing."""
        mock_settings.personal_token = ""

        with pytest.raises(ValueError) as exc_info:
            XrayClient.from_config(mock_settings)

        assert "Personal Access Token is required" in str(exc_info.value)

    def test_from_config_none_token_raises_error(self, mock_settings):
        """Test from_config raises error when token is None."""
        mock_settings.personal_token = None

        with pytest.raises(ValueError) as exc_info:
            XrayClient.from_config(mock_settings)

        assert "Personal Access Token is required" in str(exc_info.value)

    def test_from_config_unsupported_auth_type(self, mock_settings):
        """Test from_config raises error for unsupported auth type."""
        mock_settings.auth_type = "oauth"

        with pytest.raises(ValueError) as exc_info:
            XrayClient.from_config(mock_settings)

        assert "Unsupported authentication type" in str(exc_info.value)

    def test_client_property_returns_async_client(self):
        """Test client property returns the underlying AsyncClient."""
        mock_async_client = MagicMock(spec=httpx.AsyncClient)
        client = XrayClient(mock_async_client)

        assert client.client is mock_async_client

    async def test_close_calls_aclose(self):
        """Test close method calls aclose on the underlying client."""
        mock_async_client = AsyncMock(spec=httpx.AsyncClient)
        client = XrayClient(mock_async_client)

        await client.close()

        mock_async_client.aclose.assert_awaited_once()

    def test_init_stores_client(self):
        """Test __init__ stores the provided client."""
        mock_async_client = MagicMock(spec=httpx.AsyncClient)
        client = XrayClient(mock_async_client)

        assert client._client is mock_async_client


class TestXrayClientIntegration:
    """Integration-style tests for XrayClient (with mocked HTTP)."""

    @pytest.fixture
    def settings_with_custom_timeout(self) -> MagicMock:
        """Create mock settings with custom timeout."""
        settings = MagicMock(spec=AppSettings)
        settings.url = "https://xray.example.com/api"
        settings.auth_type = "pat"
        settings.personal_token = "integration-test-token"
        settings.timeout = 60.0
        return settings

    def test_client_configured_for_api_calls(self, settings_with_custom_timeout):
        """Test client is properly configured for making API calls."""
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_instance = MagicMock()
            mock_async_client.return_value = mock_instance

            client = XrayClient.from_config(settings_with_custom_timeout)

            # Verify configuration
            call_kwargs = mock_async_client.call_args.kwargs
            assert call_kwargs["base_url"] == "https://xray.example.com/api"
            assert "Bearer integration-test-token" in call_kwargs["headers"]["Authorization"]

            # Verify client is accessible
            assert client.client is mock_instance
