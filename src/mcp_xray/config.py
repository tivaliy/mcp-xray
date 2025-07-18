from functools import lru_cache
from typing import Annotated, Literal

from fastmcp.server.openapi import MCPType, RouteMap
from pydantic import BaseModel, BeforeValidator, Field, HttpUrl, TypeAdapter, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Create a custom URL type that validates as HttpUrl but stores as str
http_url_adapter = TypeAdapter(HttpUrl)
Url = Annotated[str, BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))]


class AppSettings(BaseSettings):
    """Application settings for the MCP-Xray integration.

    This class handles the configuration for connecting to the Xray API.
    It supports loading configuration from environment variables.

    Attributes:
        url: Base URL for the Xray API
        auth_type: Authentication type, currently only "pat" is supported
        personal_token: Personal Access Token for Xray Server/Data Center
        openapi_spec: Path to the OpenAPI specification file
    """

    # Base URL for the Xray API
    url: Url = Field(..., description="Base URL for the Xray API")
    # Authentication type, only "pat" (Personal Access Token) is supported currently
    auth_type: Literal["pat"] = "pat"
    # Personal Access Token for Xray Server/Data Center
    personal_token: str = Field(..., description="Personal Access Token for Xray API")
    # Used to filter out write operations in the API
    read_only: bool = Field(
        default=False,
        description="Whether to use the Xray API in read-only mode.",
    )
    # OpenAPI spec file path or URL
    openapi_spec: str = Field(
        ..., description="Path to the OpenAPI specification file: URL or local path"
    )
    # Optional configuration file
    config_file: str | None = Field(
        None,
        description="Path to the configuration file",
    )

    # Xray client configuration
    timeout: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="XRAY_",  # Environment variables should be prefixed with XRAY_
        frozen=True,
    )


class MCPConfiguration(BaseModel):
    """Configuration for the MCP"""

    mcp_names: dict[str, str] | None = Field(
        default=None,
        description="List of mappings for MCP names (originalName -> mapped_name)",
    )
    route_maps: list[RouteMap] | None = Field(
        default=None,
        description="Custom route mappings for MCP components",
    )

    @field_validator("route_maps", mode="before")
    @classmethod
    def build_route_maps(cls, v: list[object] | None) -> list[RouteMap] | None:
        if v is None:
            return v
        result = []
        for item in v:
            if isinstance(item, RouteMap):
                result.append(item)
            elif isinstance(item, dict):
                # Convert mcp_type to MCPType if it's a string
                if "mcp_type" in item and isinstance(item["mcp_type"], str):
                    try:
                        item["mcp_type"] = MCPType[item["mcp_type"]]
                    except KeyError as err:
                        msg = (
                            f"Invalid MCPType: {item['mcp_type']}. Supported types are: "
                            f"{list(MCPType.__members__.keys())}"
                        )
                        raise ValueError(msg) from err
                # Convert mcp_tags and tags to sets if they are lists
                for key in ("mcp_tags", "tags"):
                    if key in item and isinstance(item[key], list):
                        item[key] = set(item[key])
                # Create RouteMap instance
                try:
                    result.append(RouteMap(**item))
                except TypeError as err:
                    msg = f"Error creating RouteMap from item: {item}. Error: {err}"
                    raise ValueError(msg) from err
            else:
                msg = f"Invalid type for route_map: {type(item)}"
                raise TypeError(msg)
        return result


@lru_cache
def get_app_settings() -> AppSettings:
    """Get the Xray configuration settings.

    This function caches the settings to avoid reloading them multiple times.
    It uses environment variables prefixed with XRAY_ to populate the configuration.

    Returns:
        An instance of XrayConfig with the loaded settings.
    """
    return AppSettings()  # type: ignore[call-arg]
