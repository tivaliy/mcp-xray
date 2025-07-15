from functools import lru_cache
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, HttpUrl, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict

# Create a custom URL type that validates as HttpUrl but stores as str
http_url_adapter = TypeAdapter(HttpUrl)
Url = Annotated[str, BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))]


class XrayConfig(BaseSettings):
    """Xray API configuration.

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
    # OpenAPI spec file path or URL
    openapi_spec: str = Field(
        ..., description="Path to the OpenAPI specification file: URL or local path"
    )
    # Xray client configuration
    timeout: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="XRAY_",
        frozen=True,
    )


@lru_cache
def get_xray_config() -> XrayConfig:
    """Get the Xray configuration settings.

    This function caches the settings to avoid reloading them multiple times.
    It uses environment variables prefixed with XRAY_ to populate the configuration.

    Returns:
        An instance of XrayConfig with the loaded settings.
    """
    return XrayConfig()  # type: ignore[call-arg]
