import asyncio
import logging
import os
import sys
from typing import Any

import click

from mcp_xray import __version__
from mcp_xray.server import create_mcp
from mcp_xray.utils import setup_logging


@click.version_option(version=__version__, prog_name="mcp-xray")
@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity of logging output. Use multiple times for more verbosity.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"], case_sensitive=False),
    default="stdio",
    help="Transport type (stdio, sse, or streamable-http)",
)
@click.option(
    "--port",
    default=8000,
    help="Port to listen on for SSE or Streamable HTTP transport",
)
@click.option(
    "--host",
    default="0.0.0.0",  # noqa: S104
    help="Host to bind to for SSE or Streamable HTTP transport (default: 0.0.0.0)",
)
@click.option(
    "--path",
    default="/mcp",
    help="Path for Streamable HTTP transport (e.g., /mcp).",
)
@click.option(
    "--xray-url",
    help="Jira Xray URL (e.g., https://your-domain.atlassian.net/jira)",
    required=True,
)
@click.option(
    "--xray-personal-token",
    help="Jira Xray Personal Access Token (for Xray Server/Data Center)",
    required=True,
)
@click.option(
    "--xray-openapi-spec",
    type=str,
    required=True,
    help="Path or URL to the OpenAPI spec file for Xray API",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the configuration file (YAML/JSON)",
)
@click.option(
    "--read-only/--no-read-only",
    is_flag=True,
    default=False,
    help="Run the MCP-Xray in read-only mode (no modifications allowed).",
)
def main(
    verbose: int,
    transport: str,
    port: int,
    host: str,
    path: str,
    xray_url: str,
    xray_personal_token: str,
    xray_openapi_spec: str,
    config_file: str | None = None,
    *,
    read_only: bool = False,
) -> None:
    """MCP-Xray Server - Xray integration for MCP."""
    # Logging level logic
    if verbose == 1:
        current_logging_level = logging.INFO
    elif verbose >= 2:  # -vv or more
        current_logging_level = logging.DEBUG
    else:
        current_logging_level = logging.WARNING

    logging_stream = sys.stderr

    logger = setup_logging(current_logging_level, logging_stream)
    logger.debug(f"Logging level set to: {logging.getLevelName(current_logging_level)}")
    logger.debug(f"Logging stream set to: {'stdout' if logging_stream is sys.stdout else 'stderr'}")

    def was_option_provided(ctx: click.Context, param_name: str) -> bool:
        return (
            ctx.get_parameter_source(param_name) != click.core.ParameterSource.DEFAULT_MAP
            and ctx.get_parameter_source(param_name) != click.core.ParameterSource.DEFAULT
        )

    click_ctx = click.get_current_context(silent=True)

    # Transport precedence
    final_transport = os.getenv("TRANSPORT", "stdio").lower()
    if click_ctx and was_option_provided(click_ctx, "transport"):
        final_transport = transport
    if final_transport not in ["stdio", "sse", "streamable-http"]:
        logger.warning(f"Invalid transport '{final_transport}' from env/default, using 'stdio'.")
        final_transport = "stdio"
    logger.debug(f"Final transport determined: {final_transport}")

    # Port precedence
    final_port = 8000
    port_env = os.getenv("PORT")
    if port_env is not None and port_env.isdigit():
        final_port = int(port_env)
    if click_ctx and was_option_provided(click_ctx, "port"):
        final_port = port
    logger.debug(f"Final port for HTTP transports: {final_port}")

    # Host precedence
    final_host: str = os.getenv("HOST", "0.0.0.0")  # noqa: S104
    if click_ctx and was_option_provided(click_ctx, "host"):
        final_host = host
    logger.debug(f"Final host for HTTP transports: {final_host}")

    # Path precedence
    final_path: str | None = os.getenv("STREAMABLE_HTTP_PATH", None)
    if click_ctx and was_option_provided(click_ctx, "path"):
        final_path = path
    logger.debug(
        f"Final path for Streamable HTTP: {final_path if final_path else 'FastMCP default'}"
    )

    # Set env vars
    if click_ctx and was_option_provided(click_ctx, "openapi_spec"):
        os.environ["XRAY_OPENAPI_SPEC"] = xray_openapi_spec
    if click_ctx and was_option_provided(click_ctx, "xray_url"):
        os.environ["XRAY_URL"] = xray_url
    if click_ctx and was_option_provided(click_ctx, "xray_personal_token"):
        os.environ["XRAY_PERSONAL_TOKEN"] = xray_personal_token
    if click_ctx and config_file and was_option_provided(click_ctx, "config_file"):
        os.environ["XRAY_CONFIG_FILE"] = config_file
    if click_ctx and was_option_provided(click_ctx, "read_only"):
        os.environ["XRAY_READ_ONLY"] = str(read_only).lower()

    # Create the FastMCP application
    mcp_app = create_mcp()

    run_kwargs: dict[str, Any] = {
        "transport": final_transport,
    }

    if final_transport == "stdio":
        logger.info("Starting server with STDIO transport.")
    elif final_transport in ["sse", "streamable-http"]:
        run_kwargs["host"] = final_host
        run_kwargs["port"] = final_port
        run_kwargs["log_level"] = logging.getLevelName(current_logging_level).lower()

        if final_path is not None:
            run_kwargs["path"] = final_path

        log_display_path = final_path
        if log_display_path is None:
            if final_transport == "sse":
                log_display_path = "/sse"
            else:
                log_display_path = "/mcp"

        logger.info(
            f"Starting server with {final_transport.upper()} transport on http://{final_host}:{final_port}{log_display_path}"
        )
    else:
        logger.error(f"Invalid transport type '{final_transport}' determined. Cannot start server.")
        sys.exit(1)

    try:
        logger.debug("Starting asyncio event loop...")
        asyncio.run(mcp_app.run_async(**run_kwargs))
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info(f"Server shutdown initiated: {type(e).__name__}")
    except Exception as e:
        logger.error(f"Server encountered an error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
