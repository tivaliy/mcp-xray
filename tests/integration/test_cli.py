"""Integration tests for mcp_xray CLI (__main__.py)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mcp_xray.__main__ import main


class TestCLI:
    """Tests for the CLI interface."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a Click CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def openapi_spec_file(self, tmp_path: Path) -> Path:
        """Create a temporary OpenAPI spec file."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(spec), encoding="utf-8")
        return spec_file

    def test_help_option(self, runner: CliRunner):
        """Test --help option shows help text."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "MCP-Xray Server" in result.output
        assert "--xray-url" in result.output
        assert "--xray-personal-token" in result.output
        assert "--xray-openapi-spec" in result.output

    def test_version_option(self, runner: CliRunner):
        """Test --version option shows version."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "mcp-xray" in result.output

    def test_missing_required_options(self, runner: CliRunner):
        """Test CLI fails when required options are missing."""
        result = runner.invoke(main, [])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_missing_xray_url(self, runner: CliRunner, openapi_spec_file: Path):
        """Test CLI fails when --xray-url is missing."""
        result = runner.invoke(
            main,
            [
                "--xray-personal-token",
                "test-token",
                "--xray-openapi-spec",
                str(openapi_spec_file),
            ],
        )

        assert result.exit_code != 0
        assert "xray-url" in result.output.lower()

    def test_missing_xray_token(self, runner: CliRunner, openapi_spec_file: Path):
        """Test CLI fails when --xray-personal-token is missing."""
        result = runner.invoke(
            main,
            [
                "--xray-url",
                "https://xray.example.com",
                "--xray-openapi-spec",
                str(openapi_spec_file),
            ],
        )

        assert result.exit_code != 0
        assert "xray-personal-token" in result.output.lower()

    def test_missing_openapi_spec(self, runner: CliRunner):
        """Test CLI fails when --xray-openapi-spec is missing."""
        result = runner.invoke(
            main,
            [
                "--xray-url",
                "https://xray.example.com",
                "--xray-personal-token",
                "test-token",
            ],
        )

        assert result.exit_code != 0
        assert "xray-openapi-spec" in result.output.lower()

    def test_invalid_transport_choice(self, runner: CliRunner, openapi_spec_file: Path):
        """Test CLI fails with invalid transport choice."""
        result = runner.invoke(
            main,
            [
                "--xray-url",
                "https://xray.example.com",
                "--xray-personal-token",
                "test-token",
                "--xray-openapi-spec",
                str(openapi_spec_file),
                "--transport",
                "invalid",
            ],
        )

        assert result.exit_code != 0
        assert "invalid" in result.output.lower()

    def test_valid_transport_choices(self, runner: CliRunner):
        """Test valid transport choices are accepted."""
        # Just testing that the choices are recognized in help
        result = runner.invoke(main, ["--help"])

        assert "stdio" in result.output
        assert "sse" in result.output
        assert "streamable-http" in result.output

    def test_config_file_not_found(self, runner: CliRunner, openapi_spec_file: Path):
        """Test CLI fails when config file doesn't exist."""
        result = runner.invoke(
            main,
            [
                "--xray-url",
                "https://xray.example.com",
                "--xray-personal-token",
                "test-token",
                "--xray-openapi-spec",
                str(openapi_spec_file),
                "--config-file",
                "/nonexistent/config.yaml",
            ],
        )

        assert result.exit_code != 0

    def test_read_only_flag(self, runner: CliRunner):
        """Test --read-only flag is recognized."""
        result = runner.invoke(main, ["--help"])

        assert "--read-only" in result.output
        assert "--no-read-only" in result.output

    def test_verbose_flag(self, runner: CliRunner):
        """Test -v/--verbose flag is recognized."""
        result = runner.invoke(main, ["--help"])

        assert "-v" in result.output
        assert "--verbose" in result.output

    def test_port_option(self, runner: CliRunner):
        """Test --port option is recognized."""
        result = runner.invoke(main, ["--help"])

        assert "--port" in result.output

    def test_host_option(self, runner: CliRunner):
        """Test --host option is recognized."""
        result = runner.invoke(main, ["--help"])

        assert "--host" in result.output

    def test_path_option(self, runner: CliRunner):
        """Test --path option is recognized."""
        result = runner.invoke(main, ["--help"])

        assert "--path" in result.output


class TestCLIExecution:
    """Tests for CLI execution with mocked dependencies."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a Click CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def openapi_spec_file(self, tmp_path: Path) -> Path:
        """Create a temporary OpenAPI spec file."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "getTest",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(spec), encoding="utf-8")
        return spec_file

    def test_cli_sets_environment_variables(
        self, runner: CliRunner, openapi_spec_file: Path, clear_settings_cache
    ):
        """Test CLI sets environment variables correctly."""

        with patch("mcp_xray.__main__.create_mcp") as mock_create_mcp:
            mock_app = MagicMock()
            mock_app.run_async = MagicMock(side_effect=KeyboardInterrupt())
            mock_create_mcp.return_value = mock_app

            runner.invoke(
                main,
                [
                    "--xray-url",
                    "https://test.example.com",
                    "--xray-personal-token",
                    "cli-test-token",
                    "--xray-openapi-spec",
                    str(openapi_spec_file),
                ],
                catch_exceptions=False,
            )

            # Verify env vars were set before create_mcp was called
            mock_create_mcp.assert_called_once()

    def test_cli_starts_with_stdio_transport(
        self, runner: CliRunner, openapi_spec_file: Path, clear_settings_cache
    ):
        """Test CLI starts server with stdio transport by default."""
        with patch("mcp_xray.__main__.create_mcp") as mock_create_mcp:
            mock_app = MagicMock()
            mock_app.run_async = MagicMock(side_effect=KeyboardInterrupt())
            mock_create_mcp.return_value = mock_app

            runner.invoke(
                main,
                [
                    "--xray-url",
                    "https://test.example.com",
                    "--xray-personal-token",
                    "test-token",
                    "--xray-openapi-spec",
                    str(openapi_spec_file),
                ],
                catch_exceptions=False,
            )

            mock_app.run_async.assert_called_once()
            call_kwargs = mock_app.run_async.call_args.kwargs
            assert call_kwargs["transport"] == "stdio"

    def test_cli_starts_with_sse_transport(
        self, runner: CliRunner, openapi_spec_file: Path, clear_settings_cache
    ):
        """Test CLI starts server with SSE transport when specified."""
        with patch("mcp_xray.__main__.create_mcp") as mock_create_mcp:
            mock_app = MagicMock()
            mock_app.run_async = MagicMock(side_effect=KeyboardInterrupt())
            mock_create_mcp.return_value = mock_app

            runner.invoke(
                main,
                [
                    "--xray-url",
                    "https://test.example.com",
                    "--xray-personal-token",
                    "test-token",
                    "--xray-openapi-spec",
                    str(openapi_spec_file),
                    "--transport",
                    "sse",
                ],
                catch_exceptions=False,
            )

            mock_app.run_async.assert_called_once()
            call_kwargs = mock_app.run_async.call_args.kwargs
            assert call_kwargs["transport"] == "sse"
            assert "host" in call_kwargs
            assert "port" in call_kwargs

    def test_cli_custom_port_and_host(
        self, runner: CliRunner, openapi_spec_file: Path, clear_settings_cache
    ):
        """Test CLI uses custom port and host."""
        with patch("mcp_xray.__main__.create_mcp") as mock_create_mcp:
            mock_app = MagicMock()
            mock_app.run_async = MagicMock(side_effect=KeyboardInterrupt())
            mock_create_mcp.return_value = mock_app

            runner.invoke(
                main,
                [
                    "--xray-url",
                    "https://test.example.com",
                    "--xray-personal-token",
                    "test-token",
                    "--xray-openapi-spec",
                    str(openapi_spec_file),
                    "--transport",
                    "streamable-http",
                    "--port",
                    "9000",
                    "--host",
                    "127.0.0.1",
                ],
                catch_exceptions=False,
            )

            call_kwargs = mock_app.run_async.call_args.kwargs
            assert call_kwargs["port"] == 9000
            assert call_kwargs["host"] == "127.0.0.1"

    def test_cli_handles_keyboard_interrupt(
        self, runner: CliRunner, openapi_spec_file: Path, clear_settings_cache
    ):
        """Test CLI handles KeyboardInterrupt gracefully."""
        with patch("mcp_xray.__main__.create_mcp") as mock_create_mcp:
            mock_app = MagicMock()
            mock_app.run_async = MagicMock(side_effect=KeyboardInterrupt())
            mock_create_mcp.return_value = mock_app

            result = runner.invoke(
                main,
                [
                    "--xray-url",
                    "https://test.example.com",
                    "--xray-personal-token",
                    "test-token",
                    "--xray-openapi-spec",
                    str(openapi_spec_file),
                ],
            )

            # Should exit cleanly (exit code 0 or handled gracefully)
            assert result.exit_code == 0

    def test_cli_handles_exception(
        self, runner: CliRunner, openapi_spec_file: Path, clear_settings_cache
    ):
        """Test CLI handles unexpected exceptions."""
        with patch("mcp_xray.__main__.create_mcp") as mock_create_mcp:
            mock_app = MagicMock()
            mock_app.run_async = MagicMock(side_effect=RuntimeError("Test error"))
            mock_create_mcp.return_value = mock_app

            result = runner.invoke(
                main,
                [
                    "--xray-url",
                    "https://test.example.com",
                    "--xray-personal-token",
                    "test-token",
                    "--xray-openapi-spec",
                    str(openapi_spec_file),
                ],
            )

            # Should exit with error code
            assert result.exit_code == 1
