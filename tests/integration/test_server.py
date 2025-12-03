"""Integration tests for mcp_xray.server module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_xray.core.config import AppSettings


class TestCreateMCP:
    """Integration tests for create_mcp function."""

    @pytest.fixture
    def openapi_spec_file(self, tmp_path: Path, sample_openapi_spec) -> Path:
        """Create a temporary OpenAPI spec file."""
        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(sample_openapi_spec), encoding="utf-8")
        return spec_file

    @pytest.fixture
    def config_file(self, tmp_path: Path) -> Path:
        """Create a temporary config file."""
        import yaml

        config = {
            "mcp_names": {"getTest": "get_test"},
            "route_maps": [{"methods": ["DELETE"], "mcp_type": "EXCLUDE"}],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config), encoding="utf-8")
        return config_file

    @pytest.fixture
    def mock_settings(self, openapi_spec_file: Path) -> MagicMock:
        """Create mock AppSettings."""
        settings = MagicMock(spec=AppSettings)
        settings.url = "https://xray.example.com"
        settings.auth_type = "pat"
        settings.personal_token = "test-token"
        settings.openapi_spec = str(openapi_spec_file)
        settings.config_file = None
        settings.read_only = False
        settings.timeout = 20.0
        return settings

    def test_create_mcp_minimal_config(self, mock_settings, clear_settings_cache):
        """Test create_mcp with minimal configuration."""
        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.client = MagicMock()
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            result = create_mcp()

            assert result is mock_mcp
            mock_xray_client.from_config.assert_called_once_with(mock_settings)
            mock_fastmcp.from_openapi.assert_called_once()

    def test_create_mcp_with_read_only_mode(self, mock_settings, clear_settings_cache):
        """Test create_mcp applies read-only route maps."""
        mock_settings.read_only = True

        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.client = MagicMock()
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            create_mcp()

            call_kwargs = mock_fastmcp.from_openapi.call_args.kwargs
            route_maps = call_kwargs.get("route_maps")
            assert route_maps is not None
            assert len(route_maps) == 1
            assert route_maps[0].methods == ["POST", "PUT", "DELETE"]

    def test_create_mcp_with_config_file(
        self, mock_settings, config_file: Path, clear_settings_cache
    ):
        """Test create_mcp loads configuration from file."""
        mock_settings.config_file = str(config_file)

        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.client = MagicMock()
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            create_mcp()

            call_kwargs = mock_fastmcp.from_openapi.call_args.kwargs
            assert call_kwargs.get("mcp_names") == {"getTest": "get_test"}

    def test_create_mcp_config_file_overrides_read_only(
        self, mock_settings, config_file: Path, clear_settings_cache
    ):
        """Test config file route_maps take precedence over read_only flag."""
        mock_settings.read_only = True
        mock_settings.config_file = str(config_file)

        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.client = MagicMock()
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            create_mcp()

            # Config file route_maps should be used, not the read-only defaults
            call_kwargs = mock_fastmcp.from_openapi.call_args.kwargs
            route_maps = call_kwargs.get("route_maps")
            assert route_maps is not None
            # Config file only excludes DELETE, not POST/PUT
            assert len(route_maps) == 1
            assert route_maps[0].methods == ["DELETE"]

    def test_create_mcp_passes_openapi_spec(self, mock_settings, clear_settings_cache):
        """Test create_mcp passes loaded OpenAPI spec to FastMCP."""
        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.client = MagicMock()
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            create_mcp()

            call_kwargs = mock_fastmcp.from_openapi.call_args.kwargs
            openapi_spec = call_kwargs.get("openapi_spec")
            assert openapi_spec is not None
            assert "openapi" in openapi_spec

    def test_create_mcp_passes_xray_client(self, mock_settings, clear_settings_cache):
        """Test create_mcp passes XrayClient to FastMCP."""
        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_http_client = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_instance.client = mock_http_client
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            create_mcp()

            call_kwargs = mock_fastmcp.from_openapi.call_args.kwargs
            assert call_kwargs.get("client") is mock_http_client

    def test_create_mcp_sets_app_name(self, mock_settings, clear_settings_cache):
        """Test create_mcp sets correct app name."""
        with (
            patch("mcp_xray.server.get_app_settings", return_value=mock_settings),
            patch("mcp_xray.server.XrayClient") as mock_xray_client,
            patch("mcp_xray.server.FastMCP") as mock_fastmcp,
        ):
            mock_client_instance = MagicMock()
            mock_client_instance.client = MagicMock()
            mock_xray_client.from_config.return_value = mock_client_instance

            mock_mcp = MagicMock()
            mock_fastmcp.from_openapi.return_value = mock_mcp

            from mcp_xray.server import create_mcp

            create_mcp()

            call_kwargs = mock_fastmcp.from_openapi.call_args.kwargs
            assert call_kwargs.get("name") == "Xray MCP"
