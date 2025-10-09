# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package (development mode)
pip install -e .

# Alternative setup with virtual environment (recommended)
python setup_mcp.py
```

### Running the Server

#### Local Development (stdio mode)
```bash
# Run the MCP server directly (stdio mode by default)
python word_mcp_server.py

# Or use the package script
word_mcp_server

# For debugging
export MCP_DEBUG=1  # Linux/macOS
set MCP_DEBUG=1     # Windows
```

#### HTTP Mode (for Azure Container Apps)
```bash
# Set environment variables for HTTP mode
export MCP_TRANSPORT=http
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_PATH=/mcp

# Run the server
python word_mcp_server.py
```

### Configuration
The server supports multiple transport modes configured via environment variables in `.env`:
- `MCP_TRANSPORT`: stdio (default), streamable-http, http, or sse
- `MCP_HOST`: Host for HTTP/SSE modes (default: 0.0.0.0)
- `MCP_PORT`: Port for HTTP/SSE modes (default: 8000)
- `MCP_PATH`: Endpoint path for HTTP mode (default: /mcp)

### Azure Container Apps Deployment

This server is configured for Azure Container Apps deployment:

#### Quick Deployment
```bash
# Simple deployment (no authentication)
./deploy-azure.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME>

# Secure deployment (with API key)
./deploy-azure-secure.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY]
```

#### Manual Deployment
```bash
# Build and push to ACR
az acr build -t word-mcp-server:latest -r <ACR_NAME> .

# Deploy to Container Apps
az containerapp create \
  --name word-mcp-server \
  --resource-group <RG_NAME> \
  --environment <ENV_NAME> \
  --image <ACR_NAME>.azurecr.io/word-mcp-server:latest \
  --ingress external --target-port 8000 \
  --min-replicas 0 --max-replicas 1 \
  --env-vars MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=8000 MCP_PATH=/mcp
```

See `AZURE_DEPLOYMENT.md` for complete deployment instructions.

## Architecture Overview

### Core Structure
The project follows a modular architecture that separates concerns into distinct layers:

- **MCP Layer** (`word_document_server/main.py`): FastMCP server initialization and tool registration. All tools are registered as MCP endpoints using the `@mcp.tool()` decorator pattern.

- **Tools Layer** (`word_document_server/tools/`): High-level MCP tool implementations that expose document operations. Each module focuses on a specific domain (documents, content, formatting, etc.) and acts as the interface between MCP and the core functionality.

- **Core Layer** (`word_document_server/core/`): Low-level document manipulation logic using python-docx. These modules contain the actual implementation details for Word document operations.

- **Utils Layer** (`word_document_server/utils/`): Shared utilities for file operations, document helpers, and common functionality used across the application.

### Key Design Patterns

1. **Tool Registration Pattern**: All MCP tools are registered in `main.py` by wrapping functions from the tools layer with `@mcp.tool()` decorators. This creates a clean separation between MCP protocol handling and business logic.

2. **Module Organization**: Each tools module corresponds to a functional domain:
   - `document_tools.py`: Document lifecycle (create, copy, convert)
   - `content_tools.py`: Content manipulation (add paragraphs, tables, images)
   - `format_tools.py`: Text and table formatting operations
   - `protection_tools.py`: Document security and protection
   - `comment_tools.py`: Comment extraction and analysis
   - `footnote_tools.py`: Footnote/endnote management

3. **Error Handling**: The application uses try-catch blocks throughout to provide meaningful error messages when document operations fail, particularly important for file access and Word document manipulation.

### Transport Architecture
The server supports multiple transport modes through FastMCP:
- **stdio**: Default mode for Claude Desktop integration
- **streamable-http**: HTTP-based transport for network communication
- **sse**: Server-Sent Events for streaming responses

Transport configuration is handled in `get_transport_config()` which reads from environment variables and validates the selected transport mode.

## Important Implementation Notes

1. **Document Operations**: All document operations use absolute paths. The server maintains no state between operations - each tool call is independent.

2. **Table Indexing**: Tables use 0-based indexing for all operations (rows, columns, table indices).

3. **Color Formats**: Colors can be specified as hex codes (without '#' prefix) or standard color names. Hex format: "FF0000" for red.

4. **Style Handling**: The server attempts to use existing Word styles when available, falling back to direct formatting when styles are missing.

5. **File Safety**: The server never automatically overwrites files - copy operations require explicit destination filenames.

## Adding New Features

When adding new document manipulation features:

1. Create the core implementation in `word_document_server/core/`
2. Add the high-level tool wrapper in appropriate file under `word_document_server/tools/`
3. Register the tool in `word_document_server/main.py` using the `@mcp.tool()` decorator
4. Follow existing patterns for error handling and parameter validation

## Dependencies

Key dependencies and their purposes:
- `fastmcp`: MCP server framework
- `python-docx`: Word document manipulation
- `msoffcrypto-tool`: Document protection/encryption
- `docx2pdf`: PDF conversion functionality
- `python-dotenv`: Environment variable management