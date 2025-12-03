"""Shared fixtures for mcp-xray tests."""

import json
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Path to test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_openapi_spec() -> dict[str, Any]:
    """Minimal valid OpenAPI 3.0 spec for testing."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "getTest",
                    "summary": "Test endpoint",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


@pytest.fixture
def sample_mcp_config() -> dict[str, Any]:
    """Sample MCPConfiguration dict for testing."""
    return {
        "mcp_names": {"getTest": "get_test", "createItem": "create_item"},
        "route_maps": [
            {"methods": ["POST", "PUT", "DELETE"], "mcp_type": "EXCLUDE"},
        ],
    }


@pytest.fixture
def temp_json_file(tmp_path: Path, sample_openapi_spec: dict[str, Any]) -> Path:
    """Create a temporary JSON file with sample OpenAPI spec."""
    file_path = tmp_path / "test_spec.json"
    file_path.write_text(json.dumps(sample_openapi_spec), encoding="utf-8")
    return file_path


@pytest.fixture
def temp_yaml_file(tmp_path: Path, sample_mcp_config: dict[str, Any]) -> Path:
    """Create a temporary YAML file with sample config."""
    import yaml

    file_path = tmp_path / "test_config.yaml"
    file_path.write_text(yaml.dump(sample_mcp_config), encoding="utf-8")
    return file_path


@pytest.fixture
def temp_invalid_json_file(tmp_path: Path) -> Path:
    """Create a temporary file with invalid JSON."""
    file_path = tmp_path / "invalid.json"
    file_path.write_text("{invalid json content", encoding="utf-8")
    return file_path


@pytest.fixture
def temp_invalid_yaml_file(tmp_path: Path) -> Path:
    """Create a temporary file with invalid YAML."""
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("invalid: yaml: content: [", encoding="utf-8")
    return file_path


@contextmanager
def env_vars(**kwargs: str | None) -> Generator[None, None, None]:
    """Context manager for temporarily setting environment variables.

    Args:
        **kwargs: Environment variable name-value pairs.
                  Use None to unset a variable.
    """
    old_values: dict[str, str | None] = {}

    for key, value in kwargs.items():
        old_values[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    try:
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


@pytest.fixture
def mock_env_vars():
    """Fixture that provides the env_vars context manager."""
    return env_vars


@pytest.fixture
def clean_env():
    """Remove all XRAY_ prefixed environment variables for clean tests."""
    xray_vars = [key for key in os.environ if key.startswith("XRAY_")]
    old_values = {key: os.environ.pop(key) for key in xray_vars}

    yield

    for key, value in old_values.items():
        os.environ[key] = value


@pytest.fixture
def app_settings_env(clean_env: None, mock_env_vars):
    """Set up minimal environment for AppSettings."""
    with mock_env_vars(
        XRAY_URL="https://xray.example.com",
        XRAY_PERSONAL_TOKEN="test-token-12345",
        XRAY_OPENAPI_SPEC="/path/to/spec.json",
    ):
        yield


@pytest.fixture
def clear_settings_cache():
    """Clear the lru_cache on get_app_settings before and after test."""
    from mcp_xray.core.config import get_app_settings

    get_app_settings.cache_clear()
    yield
    get_app_settings.cache_clear()


@pytest.fixture
def mock_httpx_client():
    """Create a mock for httpx.AsyncClient."""
    with patch("httpx.AsyncClient") as mock:
        yield mock
