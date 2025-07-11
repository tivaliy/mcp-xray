# mcp-xray

A lightweight server that bridges the [MCP](https://modelcontextprotocol.io/introduction) protocol with the Atlassian Jira Xray API. It loads an OpenAPI spec for Xray and exposes it via FastMCP, supporting multiple transports and simple configuration.

## Rationale

This project provides a simple way to interact with the Xray API using FastMCP, making it easier to develop and test applications that integrate with Jira Xray. This server is primarily intended for use with Xray **Server+DC configuration**.

For Xray Cloud it's recommended to use [GraphQL API](https://docs.getxray.app/display/XRAYCLOUD/GraphQL+API) + [mcp-graphql](https://github.com/blurrah/mcp-graphql) integration. It provides a more efficient and flexible way to interact with Xray Cloud, leveraging the capabilities of GraphQL.

Here is a Clarification on Xray APIs usage with differences and limitations: [Xray API Usage Clarification](https://docs.getxray.app/display/XRAY/Clarifications+on+APIs+usage).

## Features

- **FastMCP server** for Jira Xray API
- **Personal Access Token** authentication
- **OpenAPI spec** loading from file
- **Multiple transports:** stdio, SSE, streamable HTTP
- **Simple CLI and environment variable configuration**

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended for fast installs)
- Xray API Personal Access Token
- OpenAPI spec file for Xray

## Quick Start Guide

1. **Install dependencies**

   Sync dependencies from `pyproject.toml`:

   ```bash
   uv sync
   ```

   Install the project in editable mode:

   ```bash
   uv pip install -e .
   ```

1. **Obtain a Personal Access Token (PAT) for Xray**

   - Log in to your Jira instance with Xray installed.
   - Go to your user profile or Xray settings.
   - Find the section for API tokens or Personal Access Tokens.
   - Generate a new token and copy it. (See [Xray documentation](https://docs.getxray.app/display/XRAY/REST+API) for details.)

1. **Get the Xray OpenAPI spec**

   - Download the OpenAPI (Swagger) spec for your Xray version from your Xray server or the official documentation.
   - Save it locally, e.g., `/path/to/xray_openapi.json`.

1. **Configure and run in VS Code**

   - Open the project in VS Code.
   - Use the provided below example settings to configure the server.
   - When you start the server via the VS Code MCP extension or command palette, you will be prompted for your Xray API token securely.
   - Example configuration (can be stored in `.vscode/mcp.json`):
     ```json
     {
         "inputs": [
             {
                 "type": "promptString",
                 "id": "xray_token",
                 "description": "Xray Cloud API Token",
                 "password": true
             }
         ],
         "servers": {
             "mcp-xray": {
                 "command": "${workspaceFolder}/.venv/bin/python",
                 "args": [
                     "mcp_xray",
                     "--xray-url",
                     "https://<your-xray-instance>",
                     "--xray-personal-token",
                     "${input:xray_token}",
                     "--xray-openapi-spec",
                     "/path/to/xray_openapi.json"
                 ],
                 "type": "stdio"
             }
         }
     }
     ```
   - Adjust the `--xray-url` and `--xray-openapi-spec` as needed for your environment.
   - The token will be prompted interactively and not stored in plain text.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details
