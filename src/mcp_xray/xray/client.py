import logging

import httpx

from .config import XrayConfig

# Configure logging
logger = logging.getLogger("mcp-xray")


class XrayClient:
    """Async Xray API client wrapper."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @classmethod
    def from_config(cls, config: XrayConfig) -> "XrayClient":
        """Create an XrayAsyncClient from config."""
        if config.auth_type == "pat":
            if not config.personal_token:
                msg = "Personal Access Token is required for Xray API."
                raise ValueError(msg)
        else:
            msg = f"Unsupported authentication type: {config.auth_type}"
            raise ValueError(msg)

        # Initialize the client with the provided configuration
        logger.debug("Initializing XrayClient with Personal Access Token authentication.")
        headers = {
            "Authorization": f"Bearer {config.personal_token}",
            "Content-Type": "application/json",
        }

        client = httpx.AsyncClient(
            base_url=config.url,
            headers=headers,
            timeout=httpx.Timeout(config.timeout),
        )
        return cls(client)

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the underlying httpx.AsyncClient."""
        return self._client

    async def close(self) -> None:
        """Close the underlying httpx.AsyncClient."""
        await self._client.aclose()
