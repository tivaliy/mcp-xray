from fastmcp import FastMCP

from .utils.spec import load_openapi_spec
from .xray import XrayClient, get_xray_config


def create_mcp() -> FastMCP:
    """Create a FastMCP app"""

    # Initialize the Xray configuration
    xray_config = get_xray_config()

    # Initialize the Xray client
    xray_client = XrayClient.from_config(xray_config)

    # Load OpenAPI spec (dict) from URL or file path
    openapi_spec = load_openapi_spec(xray_config.openapi_spec)

    # Create the FastMCP application
    mcp_app: FastMCP = FastMCP.from_openapi(
        name="Xray MCP",
        client=xray_client.client,  # Pass the underlying httpx.AsyncClient
        openapi_spec=openapi_spec,
    )

    return mcp_app
