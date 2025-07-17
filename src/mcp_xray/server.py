from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from .config import get_xray_config
from .utils import DataReader
from .xray import XrayClient


def create_mcp() -> FastMCP:
    """Create a FastMCP app"""

    # Initialize the Xray configuration
    xray_config = get_xray_config()

    # Initialize the Xray client
    xray_client = XrayClient.from_config(xray_config)

    # Initialize the DataReader
    dl_manager = DataReader()

    # Load OpenAPI spec from either URL or file path
    openapi_spec = dl_manager.load_from(xray_config.openapi_spec)

    # If MCP names mapping file is provided, load it
    mcp_names_filepath = xray_config.mcp_names_file
    mcp_names = dl_manager.load_from(mcp_names_filepath) if mcp_names_filepath else None

    # TODO: Add RouteMapsBuilder in future to handle different filtering flows
    route_maps: list[RouteMap] | None = (
        [RouteMap(methods=["POST", "PUT", "DELETE"], mcp_type=MCPType.EXCLUDE)]
        if xray_config.read_only
        else None
    )

    # Create the FastMCP application
    mcp_app: FastMCP = FastMCP.from_openapi(
        name="Xray MCP",
        client=xray_client.client,  # Pass the underlying httpx.AsyncClient
        route_maps=route_maps,
        openapi_spec=openapi_spec,
        mcp_names=mcp_names,
    )

    return mcp_app
