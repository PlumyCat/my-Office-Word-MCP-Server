"""
FastAPI wrapper for Create Propal.
Profile: create-propal
Use case: Bot de génération de propositions Microsoft 365

This is a LIGHT version with only 15 tools.
"""

import os
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from dotenv import load_dotenv

# Import only necessary tool modules
from word_document_server.tools import (
    document_tools,
    content_tools,
    format_tools,
    template_tools,
    advanced_replace_tools
)

load_dotenv()

app = FastAPI(
    title="Create Propal",
    description="Génération de propositions commerciales depuis templates",
    version="1.0-profile"
)

API_KEY = os.getenv("API_KEY", "")

def validate_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    code: Optional[str] = Query(None)
):
    """Validate API key."""
    if not API_KEY:
        return True
    provided_key = x_api_key or code
    if not provided_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing API key")
    if provided_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")
    return True

# Import full connector wrapper routes
# (This re-uses the complete routing logic from connector_wrapper.py)
from connector_wrapper import (
    list_all_templates_endpoint,
    list_all_documents_endpoint,
    handle_post,
    handle_get
)

# Register special endpoints
app.get("/api/list/all/templates")(list_all_templates_endpoint)
app.get("/api/list/all/documents")(list_all_documents_endpoint)

# Register generic handlers
app.post("/api/{path:path}")(handle_post)
app.get("/api/{path:path}")(handle_get)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Create Propal",
        "profile": "create-propal",
        "description": "Génération de propositions commerciales depuis templates",
        "use_case": "Bot de génération de propositions Microsoft 365",
        "tools_available": 15,
        "swagger": "/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
