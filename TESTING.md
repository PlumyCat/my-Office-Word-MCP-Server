# Testing the Word MCP Server

This guide explains how to test the MCP server with different applications and configurations.

## Quick Start Configurations

### 1. Test with Claude Desktop (Local)

**Setup:**
```bash
# Use the Claude Desktop configuration
cp .env.claude .env

# Start the server (it will run in stdio mode)
python word_mcp_server.py
```

**Configure Claude Desktop:**

macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "word-document-server": {
      "command": "python",
      "args": ["/absolute/path/to/word_mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop and the server will be available.

---

### 2. Test with HTTP/API (Postman, Insomnia, curl)

**Setup:**
```bash
# Use the HTTP testing configuration
cp .env.http-test .env

# Start the server
python word_mcp_server.py
```

**Test with curl:**
```bash
# Check server is running
curl http://localhost:8000/mcp

# With authentication (if API_KEY is set in .env)
curl http://localhost:8000/mcp \
  -H "X-API-Key: test-local-key-123"

# List available tools
curl http://localhost:8000/mcp \
  -H "X-API-Key: test-local-key-123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

**Test with Postman/Insomnia:**
1. Create new request: `GET http://localhost:8000/mcp`
2. Add header: `X-API-Key: test-local-key-123`
3. Send request

---

### 3. Test with MCP Inspector (Visual Testing)

**Setup:**
```bash
# Install MCP Inspector (first time only)
npm install -g @modelcontextprotocol/inspector

# Start inspector (it will start the server automatically)
npx @modelcontextprotocol/inspector python word_mcp_server.py
```

Open browser at: http://localhost:5173

You'll get a web interface to test all MCP tools interactively.

---

### 4. Test with Custom Application

**JavaScript/TypeScript:**
```typescript
// Using fetch
const response = await fetch('http://localhost:8000/mcp', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'test-local-key-123'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'create_document',
      arguments: {
        filename: 'test.docx',
        title: 'Test Document'
      }
    }
  })
});

const result = await response.json();
console.log(result);
```

**Python:**
```python
import requests

# Call a tool
response = requests.post(
    'http://localhost:8000/mcp',
    headers={'X-API-Key': 'test-local-key-123'},
    json={
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/call',
        'params': {
            'name': 'create_document',
            'arguments': {
                'filename': 'test.docx',
                'title': 'Test Document'
            }
        }
    }
)

print(response.json())
```

**C#/.NET:**
```csharp
using System.Net.Http;
using System.Text.Json;

var client = new HttpClient();
client.DefaultRequestHeaders.Add("X-API-Key", "test-local-key-123");

var request = new
{
    jsonrpc = "2.0",
    id = 1,
    method = "tools/call",
    @params = new
    {
        name = "create_document",
        arguments = new
        {
            filename = "test.docx",
            title = "Test Document"
        }
    }
};

var response = await client.PostAsJsonAsync(
    "http://localhost:8000/mcp",
    request
);

var result = await response.Content.ReadAsStringAsync();
Console.WriteLine(result);
```

---

## Configuration Files

### Available Configurations

- **`.env.claude`** - For Claude Desktop (stdio mode)
- **`.env.http-test`** - For HTTP testing with authentication
- **`.env.example`** - Template with all options

### Switch Configurations Quickly

```bash
# Use Claude Desktop mode
cp .env.claude .env

# Use HTTP testing mode
cp .env.http-test .env

# Back to your custom config
cp .env.example .env
# Edit .env with your settings
```

---

## Testing Checklist

### Basic Functionality
- [ ] Server starts without errors
- [ ] Can connect to server (curl/browser)
- [ ] Authentication works (if enabled)
- [ ] Can list available tools
- [ ] Can create a document
- [ ] Can read a document

### Authentication
- [ ] Requests without API key are rejected (if enabled)
- [ ] Requests with wrong API key are rejected
- [ ] Requests with correct API key succeed

### Azure Blob Storage (if configured)
- [ ] Can upload documents to blob storage
- [ ] Can list documents from blob storage
- [ ] Can download documents
- [ ] TTL cleanup works

---

## Troubleshooting

### Server won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check .env file exists
ls -la .env

# Check for errors
MCP_DEBUG=1 python word_mcp_server.py
```

### Connection refused
```bash
# Check if server is running
ps aux | grep word_mcp_server

# Check port is not in use
lsof -i :8000

# Check firewall settings
```

### Authentication issues
```bash
# Verify API key in .env
cat .env | grep API_KEY

# Test without authentication first
# Remove or comment out API_KEY in .env
```

### Can't create documents
```bash
# Check file permissions
ls -la $(pwd)

# Check Azure Storage credentials (if using blob storage)
# Verify AZURE_STORAGE_CONNECTION_STRING is valid
```

---

## Development Testing

For active development, use this workflow:

```bash
# Terminal 1: Run server with auto-reload
MCP_DEBUG=1 python word_mcp_server.py

# Terminal 2: Test changes
curl http://localhost:8000/mcp \
  -H "X-API-Key: test-local-key-123"
```

---

## Production Testing

Before deploying to Azure, test the production configuration:

```bash
# Set production-like environment variables
export MCP_TRANSPORT=http
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export API_KEY="your-production-key"

# Run server
python word_mcp_server.py

# Test from another machine
curl http://YOUR_LOCAL_IP:8000/mcp \
  -H "X-API-Key: your-production-key"
```

---

## Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Azure Blob Storage Docs](https://docs.microsoft.com/azure/storage/blobs/)
