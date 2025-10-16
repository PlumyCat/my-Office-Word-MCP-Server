"""
Word Document Proposal Generator - REST API Connector
Creates commercial proposals from templates with variable replacement and table management.

Designed for Microsoft Copilot Studio integration.
"""

import os
import json
import inspect
from fastapi import FastAPI, HTTPException, Query, Body, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model
from typing import Optional, Dict, Any, get_type_hints
from dotenv import load_dotenv

# Import MCP tool modules
from word_document_server.tools import (
    document_tools,
    content_tools,
    format_tools,
    template_tools,
)

load_dotenv()

app = FastAPI(
    title="Word Document Proposal Generator",
    description="Create commercial proposals from templates - Microsoft Copilot Studio integration",
    version="1.0"
)

def shorten_response(response: str) -> str:
    """
    Shorten response to minimal format to avoid Copilot Studio content filtering.
    Keeps only: ok/error + URL (if present).
    """
    # Debug mode: return full response
    if os.getenv("DEBUG_MODE", "").lower() in ["true", "1", "yes"]:
        return response

    if not response or not isinstance(response, str):
        return str(response)

    # Extract URL if present (Azure Blob Storage URL pattern)
    url = None
    import re
    url_match = re.search(r'https://[^\s]+\.blob\.core\.windows\.net/[^\s]+', response)
    if url_match:
        url = url_match.group(0)

    # Check if error
    if any(word in response.lower() for word in ['error', 'failed', 'invalid', 'not found', 'does not exist']):
        # Extract just the error type
        if 'not found' in response.lower():
            return "error: not found"
        elif 'invalid' in response.lower():
            return "error: invalid"
        else:
            return "error"

    # Success case
    if url:
        return f"ok\n{url}"
    else:
        return "ok"

# API Key validation
API_KEY = os.getenv("API_KEY", "")

def validate_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    code: Optional[str] = Query(None)
):
    """Validate API key from header (X-API-Key) or query parameter (code)."""
    if not API_KEY:
        return True

    provided_key = x_api_key or code

    if not provided_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing API key"
        )

    if provided_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")

    return True


# Tool module registry
TOOL_MODULES = {
    "document": document_tools,
    "content": content_tools,
    "format": format_tools,
    "template": template_tools,
}


def find_tool_function(func_name: str):
    """Find a tool function by name across all modules."""
    # Search in tool modules
    for module_name, module in TOOL_MODULES.items():
        if hasattr(module, func_name):
            func = getattr(module, func_name)
            # Accept both sync and async functions
            return func
    return None


# Special wrapper endpoints (MUST BE BEFORE catch-all routes)
@app.get("/api/list/all/templates")
async def list_all_templates_endpoint(auth: bool = Depends(validate_api_key)):
    """List ALL available templates. No parameters needed."""
    try:
        result = await template_tools.list_document_templates("")
        return JSONResponse(content={"result": shorten_response(result)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list/all/documents")
async def list_all_documents_endpoint(auth: bool = Depends(validate_api_key)):
    """List ALL Word documents in storage. No parameters needed."""
    try:
        result = await document_tools.list_available_documents(".")
        return JSONResponse(content={"result": shorten_response(result)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Generic POST handler (catch-all for other endpoints)
@app.post("/api/{path:path}")
async def handle_post(path: str, body: Dict[Any, Any] = Body(...), auth: bool = Depends(validate_api_key)):
    """Generic POST endpoint handler - routes to appropriate tool function."""
    # Convert path to function name: add/paragraph -> add_paragraph
    func_name = path.replace('/', '_')

    # Special mappings for renamed endpoints
    if func_name == 'template_remove':
        func_name = 'delete_document_template'

    func = find_tool_function(func_name)
    if not func:
        raise HTTPException(status_code=404, detail=f"Tool not found: {func_name}")

    try:
        # Call the function with body parameters (async or sync)
        if inspect.iscoroutinefunction(func):
            result = await func(**body)
        else:
            result = func(**body)
        return JSONResponse(content={"result": shorten_response(result)})
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Generic GET handler (catch-all for other endpoints)
@app.get("/api/{path:path}")
async def handle_get(path: str, auth: bool = Depends(validate_api_key)):
    """Generic GET endpoint handler - routes to appropriate tool function."""
    # Convert path to function name: list/document/templates -> list_document_templates
    func_name = path.replace('/', '_')

    func = find_tool_function(func_name)
    if not func:
        raise HTTPException(status_code=404, detail=f"Tool not found: {func_name}")

    try:
        # Get function signature to extract parameters
        sig = inspect.signature(func)

        # For GET requests, parameters usually have defaults or are optional
        # Try calling with no parameters first
        if all(p.default != inspect.Parameter.empty for p in sig.parameters.values()):
            # Call function (async or sync)
            if inspect.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()
        else:
            # If requires parameters, return error
            raise HTTPException(
                status_code=400,
                detail=f"Function {func_name} requires parameters. Use POST instead."
            )

        return JSONResponse(content={"result": shorten_response(result)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint - connector info."""
    # Count available tools
    tool_count = sum(
        1 for module in TOOL_MODULES.values()
        for name, func in inspect.getmembers(module, inspect.isfunction)
        if inspect.iscoroutinefunction(func) and not name.startswith('_')
    )

    return {
        "name": "Word Document Proposal Generator",
        "version": "1.0",
        "description": f"REST API for proposal generation - {tool_count} tools",
        "swagger": "/openapi.json",
        "tools_available": tool_count
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
