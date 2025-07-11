import os
import pathlib
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


@dataclass(frozen=True)
class XrayConfig:
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
    url: str
    # Authentication type, only "pat" (Personal Access Token) is supported currently
    auth_type: Literal["pat"]
    # Personal Access Token for Xray Server/Data Center
    personal_token: str
    # OpenAPI spec file path
    openapi_spec: str

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        object.__setattr__(self, "url", self.url.rstrip("/"))

        # Validate URL format
        parsed_url = urlparse(self.url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            msg = f"Invalid URL format: {self.url}"
            raise ValueError(msg)

    @classmethod
    def from_env(cls) -> "XrayConfig":
        """Create an XrayConfig instance from environment variables.

        Returns:
            An instance of XrayConfig

        Raises:
            ValueError: If any required environment variable is missing
        """
        url = os.getenv("XRAY_URL")
        if not url:
            msg = "XRAY_URL environment variable is required."
            raise ValueError(msg)

        personal_token = os.getenv("XRAY_PERSONAL_TOKEN")
        if not personal_token:
            msg = "XRAY_PERSONAL_TOKEN environment variable is required."
            raise ValueError(msg)

        openapi_spec = os.getenv("XRAY_OPENAPI_SPEC")
        if not openapi_spec:
            msg = "XRAY_OPENAPI_SPEC environment variable is required."
            raise ValueError(msg)

        return cls(
            url=url,
            auth_type="pat",
            personal_token=personal_token,
            openapi_spec=openapi_spec,
        )

    def is_spec_file(self) -> bool:
        """Check if the OpenAPI spec is a file path.

        Returns:
            True if the spec is a file path, False if it's a URL
        """
        parsed = urlparse(self.openapi_spec)
        return not parsed.scheme or parsed.scheme == "file"

    def get_spec_path(self) -> pathlib.Path:
        """Get the OpenAPI spec as a Path object if it's a file.

        Returns:
            Path object representing the spec file

        Raises:
            ValueError: If the spec is not a file path
        """
        if not self.is_spec_file():
            msg = f"The OpenAPI spec is not a file path: {self.openapi_spec}"
            raise ValueError(msg)

        return pathlib.Path(self.openapi_spec)
