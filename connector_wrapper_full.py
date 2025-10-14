"""
FastAPI wrapper to expose ALL Word MCP tools as REST endpoints for Copilot Studio.
Auto-routes requests to appropriate tool modules.
"""

import os
import json
import inspect
from fastapi import FastAPI, HTTPException, Query, Body, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model
from typing import Optional, Dict, Any, get_type_hints
from dotenv import load_dotenv

# Import ALL MCP tool modules
from word_document_server.tools import (
    document_tools,
    content_tools,
    format_tools,
    protection_tools,
    footnote_tools,
    extended_document_tools,
    comment_tools,
    template_tools,
    advanced_replace_tools
)

load_dotenv()

app = FastAPI(
    title="Word Document MCP Connector - Complete",
    description="REST API wrapper for Word MCP Server - All 75+ tools",
    version="2.0"
)

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
    "protection": protection_tools,
    "footnote": footnote_tools,
    "extended": extended_document_tools,
    "comment": comment_tools,
    "template": template_tools,
    "advanced": advanced_replace_tools,
}


def find_tool_function(func_name: str):
    """Find a tool function by name across all modules."""
    for module_name, module in TOOL_MODULES.items():
        if hasattr(module, func_name):
            func = getattr(module, func_name)
            if inspect.iscoroutinefunction(func):
                return func
    return None


# Generic POST handler
@app.post("/api/{path:path}")
async def handle_post(path: str, body: Dict[Any, Any] = Body(...), auth: bool = Depends(validate_api_key)):
    """Generic POST endpoint handler - routes to appropriate tool function."""
    # Convert path to function name: /add/paragraph -> add_paragraph
    func_name = path.replace('/', '_')

    func = find_tool_function(func_name)
    if not func:
        raise HTTPException(status_code=404, detail=f"Tool not found: {func_name}")

    try:
        # Call the async function with body parameters
        result = await func(**body)
        return JSONResponse(content={"result": result})
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Generic GET handler
@app.get("/api/{path:path}")
async def handle_get(path: str, auth: bool = Depends(validate_api_key)):
    """Generic GET endpoint handler - routes to appropriate tool function."""
    # Convert path to function name
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
            result = await func()
        else:
            # If requires parameters, return error
            raise HTTPException(
                status_code=400,
                detail=f"Function {func_name} requires parameters. Use POST instead."
            )

        return JSONResponse(content={"result": result})
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
        "name": "Word Document MCP Connector - Complete",
        "version": "2.0",
        "description": f"REST API wrapper with {tool_count} tools",
        "swagger": "/openapi.json",
        "tools_available": tool_count
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
