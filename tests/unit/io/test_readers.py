"""Tests for mcp_xray.io.readers module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_xray.io.readers import (
    DataReader,
    JsonReader,
    UnsupportedExtensionError,
    YamlReader,
)


class TestJsonReader:
    """Tests for JsonReader class."""

    def test_read_valid_json(self):
        """Test reading valid JSON content."""
        reader = JsonReader()
        content = '{"key": "value", "number": 42}'
        result = reader.read_content(content)

        assert result == {"key": "value", "number": 42}

    def test_read_json_array(self):
        """Test reading JSON array."""
        reader = JsonReader()
        content = "[1, 2, 3]"
        result = reader.read_content(content)

        assert result == [1, 2, 3]

    def test_read_nested_json(self):
        """Test reading nested JSON structure."""
        reader = JsonReader()
        content = '{"outer": {"inner": {"deep": true}}}'
        result = reader.read_content(content)

        assert result == {"outer": {"inner": {"deep": True}}}

    def test_read_invalid_json(self):
        """Test reading invalid JSON raises ValueError."""
        reader = JsonReader()

        with pytest.raises(ValueError) as exc_info:
            reader.read_content("{invalid json")

        assert "Invalid JSON content" in str(exc_info.value)

    def test_read_empty_json(self):
        """Test reading empty JSON object."""
        reader = JsonReader()
        result = reader.read_content("{}")

        assert result == {}


class TestYamlReader:
    """Tests for YamlReader class."""

    def test_read_valid_yaml(self):
        """Test reading valid YAML content."""
        reader = YamlReader()
        content = "key: value\nnumber: 42"
        result = reader.read_content(content)

        assert result == {"key": "value", "number": 42}

    def test_read_yaml_list(self):
        """Test reading YAML list."""
        reader = YamlReader()
        content = "- item1\n- item2\n- item3"
        result = reader.read_content(content)

        assert result == ["item1", "item2", "item3"]

    def test_read_nested_yaml(self):
        """Test reading nested YAML structure."""
        reader = YamlReader()
        content = """
outer:
  inner:
    deep: true
"""
        result = reader.read_content(content)

        assert result == {"outer": {"inner": {"deep": True}}}

    def test_read_invalid_yaml(self):
        """Test reading invalid YAML raises ValueError."""
        reader = YamlReader()

        with pytest.raises(ValueError) as exc_info:
            reader.read_content("invalid: yaml: content: [")

        assert "Invalid YAML content" in str(exc_info.value)

    def test_read_empty_yaml(self):
        """Test reading empty YAML returns None."""
        reader = YamlReader()
        result = reader.read_content("")

        assert result is None


class TestDataReader:
    """Tests for DataReader class."""

    def test_default_readers_registered(self):
        """Test that default readers are registered."""
        reader = DataReader()

        assert ".json" in reader._reader_classes
        assert ".yaml" in reader._reader_classes
        assert ".yml" in reader._reader_classes

    def test_default_fetchers_registered(self):
        """Test that default fetchers are registered."""
        reader = DataReader()

        assert "file" in reader._fetcher_classes
        assert "http" in reader._fetcher_classes
        assert "https" in reader._fetcher_classes

    def test_load_from_json_file(self, temp_json_file: Path, sample_openapi_spec):
        """Test loading from a JSON file."""
        reader = DataReader()
        result = reader.load_from(str(temp_json_file))

        assert result["openapi"] == sample_openapi_spec["openapi"]
        assert result["info"]["title"] == sample_openapi_spec["info"]["title"]

    def test_load_from_yaml_file(self, temp_yaml_file: Path, sample_mcp_config):
        """Test loading from a YAML file."""
        reader = DataReader()
        result = reader.load_from(str(temp_yaml_file))

        assert result["mcp_names"] == sample_mcp_config["mcp_names"]

    def test_load_from_unsupported_extension(self, tmp_path: Path):
        """Test loading from unsupported extension raises error."""
        file_path = tmp_path / "test.xyz"
        file_path.write_text("content", encoding="utf-8")

        reader = DataReader()

        with pytest.raises(UnsupportedExtensionError) as exc_info:
            reader.load_from(str(file_path))

        assert "No reader registered for extension: .xyz" in str(exc_info.value)

    def test_load_from_unsupported_scheme_treated_as_file(self):
        """Test loading from unsupported URL scheme is treated as local file path."""
        reader = DataReader()

        # Unknown schemes fall back to "file" fetcher, which will fail with FileNotFoundError
        # because "ftp://example.com/file.json" is not a valid local path
        with pytest.raises(FileNotFoundError):
            reader.load_from("ftp://example.com/file.json")

    def test_load_from_http_url(self):
        """Test loading from HTTP URL."""
        reader = DataReader()

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = '{"key": "value"}'

        with patch.object(reader, "_create_fetcher", return_value=mock_fetcher):
            result = reader.load_from("http://example.com/spec.json")

        assert result == {"key": "value"}

    def test_load_from_https_url(self):
        """Test loading from HTTPS URL."""
        reader = DataReader()

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = '{"secure": true}'

        with patch.object(reader, "_create_fetcher", return_value=mock_fetcher):
            result = reader.load_from("https://example.com/spec.json")

        assert result == {"secure": True}

    def test_load_from_local_path_directly(self, temp_json_file: Path):
        """Test loading from local file path (without file:// scheme)."""
        reader = DataReader()

        # The DataReader works with plain local paths
        result = reader.load_from(str(temp_json_file))

        assert "openapi" in result

    def test_load_from_with_validator(self, temp_json_file: Path):
        """Test loading with custom validator."""
        reader = DataReader()

        mock_validator = MagicMock()
        mock_validator.validate.return_value = {"validated": True}

        result = reader.load_from(str(temp_json_file), validator=mock_validator)

        assert result == {"validated": True}
        mock_validator.validate.assert_called_once()

    def test_load_from_with_default_validator(self, temp_json_file: Path):
        """Test loading uses default validator when none provided."""
        mock_validator = MagicMock()
        mock_validator.validate.return_value = {"default_validated": True}

        reader = DataReader(default_validator=mock_validator)
        result = reader.load_from(str(temp_json_file))

        assert result == {"default_validated": True}

    def test_register_reader(self):
        """Test registering a custom reader."""
        reader = DataReader()

        class CustomReader:
            def read_content(self, content: str) -> dict:
                return {"custom": True}

        reader.register_reader(".custom", CustomReader)

        assert ".custom" in reader._reader_classes

    def test_register_fetcher(self):
        """Test registering a custom fetcher."""
        reader = DataReader()

        class CustomFetcher:
            def fetch(self, location: str) -> str:
                return "custom content"

        reader.register_fetcher("custom", CustomFetcher)

        assert "custom" in reader._fetcher_classes

    def test_case_insensitive_extension(self, tmp_path: Path):
        """Test extension matching is case-insensitive."""
        file_path = tmp_path / "test.JSON"
        file_path.write_text('{"upper": "case"}', encoding="utf-8")

        reader = DataReader()
        result = reader.load_from(str(file_path))

        assert result == {"upper": "case"}

    def test_load_from_invalid_json_file(self, temp_invalid_json_file: Path):
        """Test loading invalid JSON file raises ValueError."""
        reader = DataReader()

        with pytest.raises(ValueError) as exc_info:
            reader.load_from(str(temp_invalid_json_file))

        assert "Invalid JSON content" in str(exc_info.value)

    def test_load_from_invalid_yaml_file(self, temp_invalid_yaml_file: Path):
        """Test loading invalid YAML file raises ValueError."""
        reader = DataReader()

        with pytest.raises(ValueError) as exc_info:
            reader.load_from(str(temp_invalid_yaml_file))

        assert "Invalid YAML content" in str(exc_info.value)

    def test_load_from_nonexistent_file(self, tmp_path: Path):
        """Test loading non-existent file raises FileNotFoundError."""
        reader = DataReader()
        non_existent = tmp_path / "does_not_exist.json"

        with pytest.raises(FileNotFoundError):
            reader.load_from(str(non_existent))
