"""Tests for mcp_xray.core.config module."""

import pytest
from pydantic import ValidationError

from mcp_xray.core.config import MCPConfiguration, get_app_settings


class TestAppSettings:
    """Tests for AppSettings configuration class."""

    def test_valid_settings_from_env(self, app_settings_env, clear_settings_cache):
        """Test AppSettings loads correctly from environment variables."""
        settings = get_app_settings()

        # URL may have trailing slash added by Pydantic HttpUrl validation
        assert settings.url.rstrip("/") == "https://xray.example.com"
        assert settings.personal_token == "test-token-12345"
        assert settings.openapi_spec == "/path/to/spec.json"
        assert settings.auth_type == "pat"
        assert settings.read_only is False
        assert settings.timeout == 20.0

    def test_url_validation_valid_http(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test that valid HTTP URLs are accepted."""
        with mock_env_vars(
            XRAY_URL="http://localhost:8080",
            XRAY_PERSONAL_TOKEN="token",
            XRAY_OPENAPI_SPEC="/spec.json",
        ):
            settings = get_app_settings()
            assert settings.url == "http://localhost:8080/"

    def test_url_validation_valid_https(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test that valid HTTPS URLs are accepted."""
        with mock_env_vars(
            XRAY_URL="https://xray.company.com/jira",
            XRAY_PERSONAL_TOKEN="token",
            XRAY_OPENAPI_SPEC="/spec.json",
        ):
            settings = get_app_settings()
            assert settings.url == "https://xray.company.com/jira"

    def test_url_validation_invalid_url(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test that invalid URLs are rejected."""
        with mock_env_vars(
            XRAY_URL="not-a-valid-url",
            XRAY_PERSONAL_TOKEN="token",
            XRAY_OPENAPI_SPEC="/spec.json",
        ):
            with pytest.raises(ValidationError) as exc_info:
                get_app_settings()
            assert "url" in str(exc_info.value).lower()

    def test_missing_required_url(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test that missing URL raises validation error."""
        with mock_env_vars(
            XRAY_PERSONAL_TOKEN="token",
            XRAY_OPENAPI_SPEC="/spec.json",
        ):
            with pytest.raises(ValidationError) as exc_info:
                get_app_settings()
            assert "url" in str(exc_info.value).lower()

    def test_missing_required_token(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test that missing token raises validation error."""
        with mock_env_vars(
            XRAY_URL="https://xray.example.com",
            XRAY_OPENAPI_SPEC="/spec.json",
        ):
            with pytest.raises(ValidationError) as exc_info:
                get_app_settings()
            assert "personal_token" in str(exc_info.value).lower()

    def test_missing_required_openapi_spec(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test that missing openapi_spec raises validation error."""
        with mock_env_vars(
            XRAY_URL="https://xray.example.com",
            XRAY_PERSONAL_TOKEN="token",
        ):
            with pytest.raises(ValidationError) as exc_info:
                get_app_settings()
            assert "openapi_spec" in str(exc_info.value).lower()

    def test_read_only_mode(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test read_only flag from environment."""
        with mock_env_vars(
            XRAY_URL="https://xray.example.com",
            XRAY_PERSONAL_TOKEN="token",
            XRAY_OPENAPI_SPEC="/spec.json",
            XRAY_READ_ONLY="true",
        ):
            settings = get_app_settings()
            assert settings.read_only is True

    def test_custom_timeout(self, clean_env, mock_env_vars, clear_settings_cache):
        """Test custom timeout value."""
        with mock_env_vars(
            XRAY_URL="https://xray.example.com",
            XRAY_PERSONAL_TOKEN="token",
            XRAY_OPENAPI_SPEC="/spec.json",
            XRAY_TIMEOUT="60.0",
        ):
            settings = get_app_settings()
            assert settings.timeout == 60.0

    def test_config_file_optional(self, app_settings_env, clear_settings_cache):
        """Test that config_file is optional."""
        settings = get_app_settings()
        assert settings.config_file is None

    def test_settings_are_cached(self, app_settings_env, clear_settings_cache):
        """Test that get_app_settings returns cached instance."""
        settings1 = get_app_settings()
        settings2 = get_app_settings()
        assert settings1 is settings2

    def test_settings_frozen(self, app_settings_env, clear_settings_cache):
        """Test that settings are immutable (frozen)."""
        settings = get_app_settings()
        with pytest.raises(ValidationError):
            settings.url = "https://new-url.com"


class TestMCPConfiguration:
    """Tests for MCPConfiguration model."""

    def test_empty_configuration(self):
        """Test creating empty MCPConfiguration."""
        config = MCPConfiguration()
        assert config.mcp_names is None
        assert config.route_maps is None

    def test_mcp_names_mapping(self):
        """Test mcp_names are stored correctly."""
        config = MCPConfiguration(mcp_names={"getTest": "get_test", "createItem": "create_item"})
        assert config.mcp_names == {"getTest": "get_test", "createItem": "create_item"}

    def test_route_maps_from_dict(self):
        """Test route_maps validation from dict."""
        config = MCPConfiguration(route_maps=[{"methods": ["POST", "PUT"], "mcp_type": "EXCLUDE"}])
        assert config.route_maps is not None
        assert len(config.route_maps) == 1
        assert config.route_maps[0].methods == ["POST", "PUT"]

    def test_route_maps_invalid_mcp_type(self):
        """Test route_maps with invalid mcp_type raises error."""
        with pytest.raises(ValueError) as exc_info:
            MCPConfiguration(route_maps=[{"methods": ["GET"], "mcp_type": "INVALID_TYPE"}])
        assert "Invalid MCPType" in str(exc_info.value)

    def test_route_maps_with_tags_as_list(self):
        """Test route_maps converts tags list to set."""
        config = MCPConfiguration(
            route_maps=[{"methods": ["GET"], "mcp_type": "TOOL", "tags": ["tag1", "tag2"]}]
        )
        assert config.route_maps is not None
        assert config.route_maps[0].tags == {"tag1", "tag2"}

    def test_route_maps_with_mcp_tags_as_list(self):
        """Test route_maps converts mcp_tags list to set."""
        config = MCPConfiguration(
            route_maps=[{"methods": ["GET"], "mcp_type": "TOOL", "mcp_tags": ["mcp1", "mcp2"]}]
        )
        assert config.route_maps is not None
        assert config.route_maps[0].mcp_tags == {"mcp1", "mcp2"}

    def test_route_maps_invalid_item_type(self):
        """Test route_maps with invalid item type raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            MCPConfiguration(route_maps=["invalid string item"])
        assert "Invalid type for route_map" in str(exc_info.value)

    def test_route_maps_none_passthrough(self):
        """Test route_maps validator handles None correctly."""
        config = MCPConfiguration(route_maps=None)
        assert config.route_maps is None

    def test_full_configuration(self, sample_mcp_config):
        """Test full configuration from dict."""
        config = MCPConfiguration(**sample_mcp_config)
        assert config.mcp_names is not None
        assert "getTest" in config.mcp_names
        assert config.route_maps is not None
        assert len(config.route_maps) == 1
