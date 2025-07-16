from fastmcp import FastMCP

from .utils.loaders import load_json
from .xray import XrayClient, get_xray_config


def create_mcp() -> FastMCP:
    """Create a FastMCP app"""

    # Initialize the Xray configuration
    xray_config = get_xray_config()

    # Initialize the Xray client
    xray_client = XrayClient.from_config(xray_config)

    # Load OpenAPI spec (dict) from URL or file path
    openapi_spec = load_json(xray_config.openapi_spec)

    # If MCP names mapping file is provided, load it
    mcp_names_filepath = xray_config.mcp_names_file
    mcp_names = load_json(mcp_names_filepath) if mcp_names_filepath else None

    # Create the FastMCP application
    mcp_app: FastMCP = FastMCP.from_openapi(
        name="Xray MCP",
        client=xray_client.client,  # Pass the underlying httpx.AsyncClient
        openapi_spec=openapi_spec,
        mcp_names=mcp_names,
    )

    return mcp_app
