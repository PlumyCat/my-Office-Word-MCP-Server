#!/bin/bash
# Deployment script for Create Propal
# Profile: create-propal

set -e

ACR_NAME="${1:-mywordmcpacr}"
RESOURCE_GROUP="${2:-my-word-mcp-rg}"
ENVIRONMENT="${3:-my-word-mcp-env}"
API_KEY="${4}"

echo "=================================================="
echo "Create Propal - Deployment"
echo "=================================================="
echo "Profile:          create-propal"
echo "ACR:              $ACR_NAME"
echo "Resource Group:   $RESOURCE_GROUP"
echo "Environment:      $ENVIRONMENT"
echo "Connector Name:   word-mcp-proposal"
echo "Tools:            15"
echo "=================================================="
echo ""

# Build and push
echo "🔨 Building profile image..."
az acr build \
  -t word-mcp-proposal:latest \
  -r $ACR_NAME \
  --file profiles/Dockerfile.create-propal \
  .

echo "✅ Image built and pushed to ACR"

# Get storage configuration from existing server
echo "🔍 Retrieving Azure Storage configuration..."
STORAGE_NAME=$(az containerapp show \
  --name word-mcp-server \
  --resource-group $RESOURCE_GROUP \
  --query "properties.template.containers[0].env[?name=='AZURE_STORAGE_ACCOUNT_NAME'].value" \
  -o tsv 2>/dev/null || echo "")

if [ -z "$STORAGE_NAME" ]; then
    echo "⚠️  Storage config not found, using defaults"
    STORAGE_NAME="mywordmcpacrstorage"
fi

echo "✅ Storage: $STORAGE_NAME"

# Deploy or update container app
if az containerapp show --name word-mcp-proposal --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "🔄 Updating existing connector..."
    az containerapp update \
      --name word-mcp-proposal \
      --resource-group $RESOURCE_GROUP \
      --image $ACR_NAME.azurecr.io/word-mcp-proposal:latest \
      --set-env-vars \
        MCP_TRANSPORT=http \
        MCP_HOST=0.0.0.0 \
        MCP_PORT=8080 \
        MCP_PATH=/mcp \
        AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME \
        API_KEY="$API_KEY"
else
    echo "🆕 Creating new connector..."
    az containerapp create \
      --name word-mcp-proposal \
      --resource-group $RESOURCE_GROUP \
      --environment $ENVIRONMENT \
      --image $ACR_NAME.azurecr.io/word-mcp-proposal:latest \
      --ingress external --target-port 8080 \
      --min-replicas 1 --max-replicas 5 \
      --registry-server $ACR_NAME.azurecr.io \
      --env-vars \
        MCP_TRANSPORT=http \
        MCP_HOST=0.0.0.0 \
        MCP_PORT=8080 \
        MCP_PATH=/mcp \
        AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME \
        API_KEY="$API_KEY"
fi

echo "✅ Connector deployed"

# Get FQDN
FQDN=$(az containerapp show \
  --name word-mcp-proposal \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=================================================="
echo "Connector URL: https://$FQDN"
echo "Swagger:       profiles/swagger-create-propal.json"
echo "Tools:         15"
echo "=================================================="
