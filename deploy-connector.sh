#!/bin/bash

# Deployment script for Word MCP Connector Wrapper to Azure Container Apps
# This creates a separate service optimized for Copilot Studio integration

set -e

# Check arguments
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY]"
    echo ""
    echo "Example:"
    echo "  $0 myacr myResourceGroup myEnvironment my-secret-key"
    exit 1
fi

ACR_NAME=$1
RESOURCE_GROUP=$2
ENVIRONMENT_NAME=$3
API_KEY=${4:-""}

CONNECTOR_NAME="word-mcp-connector"
IMAGE_TAG="latest"

echo "=================================================="
echo "Word MCP Connector Deployment"
echo "=================================================="
echo "ACR:              $ACR_NAME"
echo "Resource Group:   $RESOURCE_GROUP"
echo "Environment:      $ENVIRONMENT_NAME"
echo "Connector Name:   $CONNECTOR_NAME"
echo "API Key:          ${API_KEY:+***configured***}"
echo "=================================================="

# Get Azure Storage configuration from existing MCP server
echo ""
echo "🔍 Retrieving Azure Storage configuration from existing MCP server..."
STORAGE_STRING=$(az containerapp show \
    --name word-mcp-server \
    --resource-group $RESOURCE_GROUP \
    --query "properties.template.containers[0].env[?name=='AZURE_STORAGE_CONNECTION_STRING'].value | [0]" \
    --output tsv)

if [ -z "$STORAGE_STRING" ]; then
    echo "❌ Failed to retrieve storage configuration from existing MCP server"
    echo "Make sure word-mcp-server is deployed first"
    exit 1
fi

echo "✅ Storage configuration retrieved"

# Build and push connector image
echo ""
echo "🔨 Building connector image..."
az acr build \
    --registry $ACR_NAME \
    --image $CONNECTOR_NAME:$IMAGE_TAG \
    --file Dockerfile.connector \
    .

echo "✅ Image built and pushed to ACR"

# Check if connector app already exists
echo ""
echo "🔍 Checking if connector app exists..."
if az containerapp show \
    --name $CONNECTOR_NAME \
    --resource-group $RESOURCE_GROUP \
    &> /dev/null; then

    echo "♻️  Connector app exists, updating..."

    # Build env vars array
    ENV_VARS="MCP_TRANSPORT=http PORT=8080"
    ENV_VARS="$ENV_VARS AZURE_STORAGE_CONNECTION_STRING=$STORAGE_STRING"
    if [ -n "$API_KEY" ]; then
        ENV_VARS="$ENV_VARS API_KEY=$API_KEY"
    fi

    az containerapp update \
        --name $CONNECTOR_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_NAME.azurecr.io/$CONNECTOR_NAME:$IMAGE_TAG \
        --set-env-vars $ENV_VARS

    echo "✅ Connector app updated"
else
    echo "🆕 Creating new connector app..."

    # Build env vars array
    ENV_VARS="MCP_TRANSPORT=http PORT=8080"
    ENV_VARS="$ENV_VARS AZURE_STORAGE_CONNECTION_STRING=$STORAGE_STRING"
    if [ -n "$API_KEY" ]; then
        ENV_VARS="$ENV_VARS API_KEY=$API_KEY"
    fi

    # Create container app
    az containerapp create \
        --name $CONNECTOR_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image $ACR_NAME.azurecr.io/$CONNECTOR_NAME:$IMAGE_TAG \
        --target-port 8080 \
        --ingress external \
        --min-replicas 0 \
        --max-replicas 3 \
        --cpu 0.5 \
        --memory 1.0Gi \
        --env-vars $ENV_VARS \
        --registry-server $ACR_NAME.azurecr.io

    echo "✅ Connector app created"

    # Assign managed identity and grant permissions
    echo ""
    echo "🔐 Configuring managed identity..."
    az containerapp identity assign \
        --name $CONNECTOR_NAME \
        --resource-group $RESOURCE_GROUP \
        --system-assigned

    PRINCIPAL_ID=$(az containerapp show \
        --name $CONNECTOR_NAME \
        --resource-group $RESOURCE_GROUP \
        --query identity.principalId \
        --output tsv)

    echo "✅ Managed identity assigned: $PRINCIPAL_ID"

    # Grant AcrPull permission
    ACR_ID=$(az acr show --name $ACR_NAME --query id --output tsv)
    az role assignment create \
        --assignee $PRINCIPAL_ID \
        --role AcrPull \
        --scope $ACR_ID

    echo "✅ AcrPull permission granted"
fi

# Get connector URL
echo ""
echo "🌐 Retrieving connector URL..."
CONNECTOR_URL=$(az containerapp show \
    --name $CONNECTOR_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=================================================="
echo ""
echo "Connector URL: https://$CONNECTOR_URL"
echo ""
echo "📋 Next steps for Copilot Studio integration:"
echo ""
echo "1. Update word-connector.swagger.json host to:"
echo "   \"host\": \"$CONNECTOR_URL\""
echo ""
echo "2. Import word-connector.swagger.json in Power Apps:"
echo "   - Go to Power Apps (make.powerapps.com)"
echo "   - Custom Connectors > New > Import an OpenAPI file"
echo "   - Upload word-connector.swagger.json"
echo ""
echo "3. Configure authentication:"
echo "   - API Key authentication"
echo "   - Parameter name: code"
echo "   - Parameter location: Query"
echo "   - Your API key: ${API_KEY:+***}"
echo ""
echo "4. Test endpoints in Power Apps"
echo ""
echo "5. Use in Copilot Studio:"
echo "   - Add action > Choose your custom connector"
echo "   - Configure inputs (AI will generate values)"
echo ""
echo "=================================================="
