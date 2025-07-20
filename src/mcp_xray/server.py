import logging

from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from .core import MCPConfiguration, get_app_settings
from .io import DataReader
from .io.validators import PydanticValidator
from .xray import XrayClient

logger = logging.getLogger("mcp-xray")


def create_mcp() -> FastMCP:
    """Create a FastMCP app"""

    # Initialize the application settings
    settings = get_app_settings()

    # Initialize the Xray client
    xray_client = XrayClient.from_config(settings)

    data_reader = DataReader()
    # Load OpenAPI spec from either URL or file path
    openapi_spec = data_reader.load_from(settings.openapi_spec)
    # If configuration file is provided, load it
    mcp_config: MCPConfiguration = (
        data_reader.load_from(settings.config_file, validator=PydanticValidator(MCPConfiguration))
        if settings.config_file
        # If no values are provided, use default empty configuration
        else MCPConfiguration()
    )

    if settings.read_only and mcp_config.route_maps:
        logger.warning(
            "Read-only mode is ENABLED, but 'route_maps' are defined in the configuration file "
            f"({settings.config_file}). Configuration route maps will take precedence."
        )

    # TODO: Revisit this eventually, keep it for compatibility '--read-only' flag for now
    route_maps: list[RouteMap] | None = (
        [RouteMap(methods=["POST", "PUT", "DELETE"], mcp_type=MCPType.EXCLUDE)]
        if settings.read_only and not mcp_config.route_maps
        else mcp_config.route_maps
    )

    # Create the FastMCP application
    mcp_app: FastMCP = FastMCP.from_openapi(
        name="Xray MCP",
        client=xray_client.client,  # Pass the underlying httpx.AsyncClient
        route_maps=route_maps,
        openapi_spec=openapi_spec,
        mcp_names=mcp_config.mcp_names,
    )

    return mcp_app
