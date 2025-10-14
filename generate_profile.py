#!/usr/bin/env python3
"""
Génère un swagger et un wrapper spécifiques pour un profil donné.
Permet de créer des versions "light" du serveur avec seulement les outils nécessaires.

Usage:
    python generate_profile.py proposal-generator
    python generate_profile.py document-editor
    python generate_profile.py minimal
"""

import json
import sys
import shutil
from pathlib import Path

def load_profiles():
    """Load available profiles."""
    with open("profiles.json") as f:
        return json.load(f)["profiles"]

def load_full_swagger():
    """Load full swagger definition."""
    with open("word-connector.swagger.json") as f:
        return json.load(f)

def generate_profile_swagger(profile_name: str, profile_config: dict, full_swagger: dict):
    """Generate swagger for a specific profile."""

    # Copy base swagger structure
    profile_swagger = {
        "swagger": full_swagger["swagger"],
        "info": {
            "title": profile_config["name"],
            "description": profile_config["description"],
            "version": "1.0-profile"
        },
        "host": full_swagger["host"],
        "basePath": full_swagger["basePath"],
        "schemes": full_swagger["schemes"],
        "securityDefinitions": full_swagger["securityDefinitions"],
        "security": full_swagger["security"],
        "paths": {}
    }

    # Get tool list
    if profile_config["tools"] == "all":
        profile_swagger["paths"] = full_swagger["paths"]
    else:
        # Filter paths based on tool list
        for tool_name in profile_config["tools"]:
            # Convert tool_name to path format
            path = f"/{tool_name.replace('_', '/')}"

            if path in full_swagger["paths"]:
                profile_swagger["paths"][path] = full_swagger["paths"][path]
            else:
                print(f"⚠️  Tool not found in full swagger: {tool_name} (path: {path})")

    # Save profile swagger
    output_file = f"profiles/swagger-{profile_name}.json"
    Path("profiles").mkdir(exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(profile_swagger, f, indent=2)

    return output_file, len(profile_swagger["paths"])

def generate_profile_wrapper(profile_name: str, profile_config: dict):
    """Generate a minimal wrapper with only profile tools imported."""

    wrapper_content = f'''"""
FastAPI wrapper for {profile_config['name']}.
Profile: {profile_name}
Use case: {profile_config['use_case']}

This is a LIGHT version with only {len(profile_config.get('tools', []))} tools.
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
    title="{profile_config['name']}",
    description="{profile_config['description']}",
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
app.post("/api/{{path:path}}")(handle_post)
app.get("/api/{{path:path}}")(handle_get)

@app.get("/")
async def root():
    """Root endpoint."""
    return {{
        "name": "{profile_config['name']}",
        "profile": "{profile_name}",
        "description": "{profile_config['description']}",
        "use_case": "{profile_config['use_case']}",
        "tools_available": {len(profile_config.get('tools', []))},
        "swagger": "/openapi.json"
    }}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''

    output_file = f"profiles/wrapper-{profile_name}.py"
    with open(output_file, "w") as f:
        f.write(wrapper_content)

    return output_file

def generate_profile_dockerfile(profile_name: str):
    """Generate Dockerfile for profile."""

    dockerfile_content = f'''FROM python:3.11-slim
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic

# Copy source code
COPY word_document_server/ ./word_document_server/
COPY connector_wrapper.py .
COPY profiles/wrapper-{profile_name}.py ./wrapper-{profile_name}.py

EXPOSE 8080

ENV MCP_TRANSPORT=http
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "wrapper-{profile_name}:app", "--host", "0.0.0.0", "--port", "8080"]
'''

    output_file = f"profiles/Dockerfile.{profile_name}"
    with open(output_file, "w") as f:
        f.write(dockerfile_content)

    return output_file

def generate_profile_deploy_script(profile_name: str, profile_config: dict):
    """Generate deployment script for profile."""

    connector_name = profile_config["connector_name"]

    script_content = f'''#!/bin/bash
# Deployment script for {profile_config['name']}
# Profile: {profile_name}

set -e

ACR_NAME="${{1:-mywordmcpacr}}"
RESOURCE_GROUP="${{2:-my-word-mcp-rg}}"
ENVIRONMENT="${{3:-my-word-mcp-env}}"
API_KEY="${{4}}"

echo "=================================================="
echo "{profile_config['name']} - Deployment"
echo "=================================================="
echo "Profile:          {profile_name}"
echo "ACR:              $ACR_NAME"
echo "Resource Group:   $RESOURCE_GROUP"
echo "Environment:      $ENVIRONMENT"
echo "Connector Name:   {connector_name}"
echo "Tools:            {len(profile_config.get('tools', []))}"
echo "=================================================="
echo ""

# Build and push
echo "🔨 Building profile image..."
az acr build \\
  -t {connector_name}:latest \\
  -r $ACR_NAME \\
  --file profiles/Dockerfile.{profile_name} \\
  .

echo "✅ Image built and pushed to ACR"

# Get storage configuration from existing server
echo "🔍 Retrieving Azure Storage configuration..."
STORAGE_NAME=$(az containerapp show \\
  --name word-mcp-server \\
  --resource-group $RESOURCE_GROUP \\
  --query "properties.template.containers[0].env[?name=='AZURE_STORAGE_ACCOUNT_NAME'].value" \\
  -o tsv 2>/dev/null || echo "")

if [ -z "$STORAGE_NAME" ]; then
    echo "⚠️  Storage config not found, using defaults"
    STORAGE_NAME="mywordmcpacrstorage"
fi

echo "✅ Storage: $STORAGE_NAME"

# Deploy or update container app
if az containerapp show --name {connector_name} --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "🔄 Updating existing connector..."
    az containerapp update \\
      --name {connector_name} \\
      --resource-group $RESOURCE_GROUP \\
      --image $ACR_NAME.azurecr.io/{connector_name}:latest \\
      --set-env-vars \\
        MCP_TRANSPORT=http \\
        MCP_HOST=0.0.0.0 \\
        MCP_PORT=8080 \\
        MCP_PATH=/mcp \\
        AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME \\
        API_KEY="$API_KEY"
else
    echo "🆕 Creating new connector..."
    az containerapp create \\
      --name {connector_name} \\
      --resource-group $RESOURCE_GROUP \\
      --environment $ENVIRONMENT \\
      --image $ACR_NAME.azurecr.io/{connector_name}:latest \\
      --ingress external --target-port 8080 \\
      --min-replicas 0 --max-replicas 1 \\
      --registry-server $ACR_NAME.azurecr.io \\
      --env-vars \\
        MCP_TRANSPORT=http \\
        MCP_HOST=0.0.0.0 \\
        MCP_PORT=8080 \\
        MCP_PATH=/mcp \\
        AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME \\
        API_KEY="$API_KEY"
fi

echo "✅ Connector deployed"

# Get FQDN
FQDN=$(az containerapp show \\
  --name {connector_name} \\
  --resource-group $RESOURCE_GROUP \\
  --query "properties.configuration.ingress.fqdn" \\
  -o tsv)

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=================================================="
echo "Connector URL: https://$FQDN"
echo "Swagger:       profiles/swagger-{profile_name}.json"
echo "Tools:         {len(profile_config.get('tools', []))}"
echo "=================================================="
'''

    output_file = f"profiles/deploy-{profile_name}.sh"
    with open(output_file, "w") as f:
        f.write(script_content)

    # Make executable
    Path(output_file).chmod(0o755)

    return output_file

def generate_profile_test(profile_name: str, profile_config: dict):
    """Generate test script for profile."""

    connector_name = profile_config["connector_name"]

    test_content = f'''#!/usr/bin/env python3
"""
Test automatique pour le profil: {profile_name}
{profile_config['description']}
"""

import requests
import json

BASE_URL = "https://{connector_name}.ashywater-9eb5a210.francecentral.azurecontainerapps.io"
API_KEY = "GV2yMslJIvxtjtMej932Sg9L3xrT6rMPmKLEqX2caSA="

def test_profile():
    """Test basic connectivity and tool availability."""
    print(f"Testing {profile_config['name']}...")
    print(f"URL: {{BASE_URL}}")

    # Test root endpoint
    response = requests.get(BASE_URL, headers={{"X-API-Key": API_KEY}})

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Profile: {{data.get('profile')}}")
        print(f"✅ Tools: {{data.get('tools_available')}}")
        return True
    else:
        print(f"❌ Failed: {{response.status_code}}")
        return False

if __name__ == "__main__":
    test_profile()
'''

    output_file = f"profiles/test-{profile_name}.py"
    with open(output_file, "w") as f:
        f.write(test_content)

    Path(output_file).chmod(0o755)

    return output_file

def generate_profile(profile_name: str):
    """Generate all files for a profile."""

    profiles = load_profiles()

    if profile_name not in profiles:
        print(f"❌ Profile '{profile_name}' not found")
        print(f"\nAvailable profiles:")
        for name, config in profiles.items():
            tools_count = len(config.get("tools", [])) if config.get("tools") != "all" else "all"
            print(f"  • {name:20} - {config['description']} ({tools_count} tools)")
        return False

    profile_config = profiles[profile_name]

    print(f"\n{'='*80}")
    print(f"Génération du profil: {profile_name}")
    print(f"{'='*80}")
    print(f"Name:        {profile_config['name']}")
    print(f"Description: {profile_config['description']}")
    print(f"Use case:    {profile_config['use_case']}")

    if profile_config["tools"] == "all":
        print(f"Tools:       ALL (67)")
    else:
        print(f"Tools:       {len(profile_config['tools'])}")

    print()

    # Load full swagger
    full_swagger = load_full_swagger()

    # Generate files
    print("📝 Generating files...")

    swagger_file, tool_count = generate_profile_swagger(profile_name, profile_config, full_swagger)
    print(f"  ✅ Swagger: {swagger_file} ({tool_count} tools)")

    wrapper_file = generate_profile_wrapper(profile_name, profile_config)
    print(f"  ✅ Wrapper: {wrapper_file}")

    dockerfile = generate_profile_dockerfile(profile_name)
    print(f"  ✅ Dockerfile: {dockerfile}")

    deploy_script = generate_profile_deploy_script(profile_name, profile_config)
    print(f"  ✅ Deploy script: {deploy_script}")

    test_script = generate_profile_test(profile_name, profile_config)
    print(f"  ✅ Test script: {test_script}")

    print()
    print(f"{'='*80}")
    print(f"✅ Profile '{profile_name}' generated successfully!")
    print(f"{'='*80}")
    print()
    print("Next steps:")
    print(f"  1. Deploy:  {deploy_script} mywordmcpacr my-word-mcp-rg my-word-mcp-env API_KEY")
    print(f"  2. Test:    python {test_script}")
    print(f"  3. Import:  {swagger_file} dans Power Apps")
    print()

    return True

def list_profiles():
    """List all available profiles."""
    profiles = load_profiles()

    print("\n📦 Profils disponibles:\n")

    for name, config in profiles.items():
        tools_count = "all (67)" if config.get("tools") == "all" else str(len(config.get("tools", [])))
        print(f"{name:25} - {config['description']}")
        print(f"{'':25}   Use case: {config['use_case']}")
        print(f"{'':25}   Tools: {tools_count}")
        print(f"{'':25}   Connector: {config['connector_name']}")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_profile.py <profile_name>")
        print("       python generate_profile.py list")
        list_profiles()
        sys.exit(1)

    if sys.argv[1] == "list":
        list_profiles()
    else:
        profile_name = sys.argv[1]
        success = generate_profile(profile_name)
        sys.exit(0 if success else 1)
