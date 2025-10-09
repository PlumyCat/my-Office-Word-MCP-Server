#!/bin/bash

# Deploy Office Word MCP Server to Azure Container Apps with Blob Storage
# Usage: ./deploy-azure-with-storage.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY] [TTL_HOURS]

set -e

# Validate input parameters
if [ $# -lt 3 ]; then
    echo "❌ Usage: $0 <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY] [TTL_HOURS]"
    echo ""
    echo "Arguments:"
    echo "  ACR_NAME:      Name of Azure Container Registry (required)"
    echo "  RESOURCE_GROUP: Name of the resource group (required)"
    echo "  ENVIRONMENT_NAME: Name of Container Apps environment (required)"
    echo "  API_KEY:       Optional API key for authentication"
    echo "  TTL_HOURS:     Document TTL in hours (default: 24)"
    echo ""
    echo "Example: $0 mywordmcpacr my-word-mcp-rg my-word-mcp-env"
    echo "Example with security: $0 mywordmcpacr my-word-mcp-rg my-word-mcp-env my-secret-key 48"
    exit 1
fi

ACR_NAME=$1
RESOURCE_GROUP=$2
ENVIRONMENT_NAME=$3
API_KEY=${4:-""}
TTL_HOURS=${5:-24}

# Derived variables
CONTAINER_APP_NAME="word-mcp-server"
STORAGE_ACCOUNT_NAME="${ACR_NAME}storage"  # Storage account name based on ACR name
CONTAINER_NAME="word-documents"
IMAGE_TAG="${ACR_NAME}.azurecr.io/word-mcp-server:latest"

echo "🚀 Deploying Office Word MCP Server to Azure Container Apps with Blob Storage"
echo "📋 Configuration:"
echo "   - ACR Name: $ACR_NAME"
echo "   - Resource Group: $RESOURCE_GROUP"
echo "   - Environment: $ENVIRONMENT_NAME"
echo "   - Container App: $CONTAINER_APP_NAME"
echo "   - Storage Account: $STORAGE_ACCOUNT_NAME"
echo "   - TTL Hours: $TTL_HOURS"
if [ ! -z "$API_KEY" ]; then
    echo "   - API Key: *** (configured)"
fi
echo ""

# Build and push to Azure Container Registry
echo "🏗️ Building and pushing Docker image..."
az acr build --registry $ACR_NAME --image word-mcp-server:latest .

# Create storage account if it doesn't exist
echo "💾 Setting up Azure Storage Account..."
STORAGE_EXISTS=$(az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")

if [ -z "$STORAGE_EXISTS" ]; then
    echo "   Creating storage account: $STORAGE_ACCOUNT_NAME"
    az storage account create \
        --name $STORAGE_ACCOUNT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location "France Central" \
        --sku Standard_LRS \
        --allow-blob-public-access true
else
    echo "   Storage account already exists: $STORAGE_ACCOUNT_NAME"
fi

# Create blob container
echo "   Setting up blob container..."
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT_NAME \
    --public-access blob \
    --auth-mode login 2>/dev/null || echo "   Container may already exist"

# Get storage account connection details
echo "🔑 Retrieving storage account credentials..."
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "connectionString" -o tsv)

STORAGE_KEY=$(az storage account keys list \
    --account-name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "[0].value" -o tsv)

echo "🌐 Deploying to Azure Container Apps..."

# Prepare environment variables
ENV_VARS="MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=8000 MCP_PATH=/mcp"
ENV_VARS="$ENV_VARS AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION_STRING"
ENV_VARS="$ENV_VARS AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME"
ENV_VARS="$ENV_VARS AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY"
ENV_VARS="$ENV_VARS AZURE_STORAGE_CONTAINER_NAME=$CONTAINER_NAME"
ENV_VARS="$ENV_VARS AZURE_TEMPLATES_CONTAINER_NAME=word-templates"
ENV_VARS="$ENV_VARS DOCUMENT_TTL_HOURS=$TTL_HOURS"
ENV_VARS="$ENV_VARS AZURE_STORAGE_LOG_LEVEL=INFO"  # Change to DEBUG for detailed diagnostics

# Add API key if provided
if [ ! -z "$API_KEY" ]; then
    ENV_VARS="$ENV_VARS API_KEY=$API_KEY"
fi

# Delete existing container app if it exists
EXISTING_APP=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
if [ ! -z "$EXISTING_APP" ]; then
    echo "   Deleting existing container app..."
    az containerapp delete --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes

    echo "   Waiting for deletion to complete..."
    for i in {1..30}; do
        STILL_EXISTS=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "name" -o tsv 2>/dev/null || echo "")
        if [ -z "$STILL_EXISTS" ]; then
            echo "   Deletion completed"
            break
        fi
        echo "   Waiting... ($i/30)"
        sleep 10
    done

    # Extra wait to ensure Azure backend is ready
    echo "   Waiting additional 20 seconds for Azure to be ready..."
    sleep 20
fi

# Create the container app with storage account integration
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $IMAGE_TAG \
    --registry-server ${ACR_NAME}.azurecr.io \
    --registry-identity system \
    --ingress external \
    --target-port 8000 \
    --min-replicas 0 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1.0Gi \
    --env-vars $ENV_VARS \
    --system-assigned

# Get the container app's managed identity
echo "🔐 Configuring permissions..."
PRINCIPAL_ID=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "identity.principalId" -o tsv)

# Grant ACR Pull permission
REGISTRY_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "id" -o tsv)
az role assignment create \
    --assignee $PRINCIPAL_ID \
    --role "AcrPull" \
    --scope $REGISTRY_ID

# Grant Storage Blob Data Contributor permission
STORAGE_ID=$(az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP --query "id" -o tsv)
az role assignment create \
    --assignee $PRINCIPAL_ID \
    --role "Storage Blob Data Contributor" \
    --scope $STORAGE_ID

# Get the container app URL
CONTAINER_APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 MCP Server URL: https://$CONTAINER_APP_URL/mcp"
echo "💾 Storage Account: $STORAGE_ACCOUNT_NAME"
echo "📁 Container: $CONTAINER_NAME"
echo "⏰ Document TTL: $TTL_HOURS hours"
echo ""
echo "📋 Service Information:"
echo "   - All Word documents will be stored in Azure Blob Storage"
echo "   - Documents automatically expire after $TTL_HOURS hours"
echo "   - Use 'cleanup_expired_documents' tool to manually clean up expired files"
echo "   - Use 'download_document' tool to get download URLs for documents"
echo ""

if [ ! -z "$API_KEY" ]; then
    echo "🔐 API Key is configured. Include 'X-API-Key: $API_KEY' header in requests."
    echo ""
fi

echo "🧪 Test your deployment:"
echo "   curl -X GET \"https://$CONTAINER_APP_URL/mcp\" -H \"Accept: text/event-stream\""
echo ""
echo "📖 Available MCP tools:"
echo "   - create_document: Create new Word documents"
echo "   - list_available_documents: List stored documents with URLs"
echo "   - download_document: Get download URL for a document"
echo "   - cleanup_expired_documents: Clean up expired documents"
echo "   - debug_storage: Debug storage configuration and show all files"
echo "   - check_document_exists: Check if document exists with diagnostics"
echo "   - All other existing document manipulation tools..."
echo ""
echo "🐞 Debugging:"
echo "   - Use 'debug_storage' tool to check storage configuration"
echo "   - Use 'check_document_exists' to diagnose missing document issues"
echo "   - Set AZURE_STORAGE_LOG_LEVEL=DEBUG for detailed logs (requires redeploy)"