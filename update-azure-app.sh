#!/bin/bash
# Update Azure Container App - image and/or environment variables
# Usage: ./update-azure-app.sh <ACR_NAME> <RESOURCE_GROUP> [--env-only] [--storage-account <NAME>]

set -e

CONTAINER_APP_NAME="word-mcp-server"
UPDATE_IMAGE=true
UPDATE_ENV=false
STORAGE_ACCOUNT_NAME=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env-only)
            UPDATE_IMAGE=false
            UPDATE_ENV=true
            shift
            ;;
        --storage-account)
            STORAGE_ACCOUNT_NAME="$2"
            UPDATE_ENV=true
            shift 2
            ;;
        *)
            if [ -z "$ACR_NAME" ]; then
                ACR_NAME=$1
            elif [ -z "$RESOURCE_GROUP" ]; then
                RESOURCE_GROUP=$1
            fi
            shift
            ;;
    esac
done

if [ -z "$ACR_NAME" ] || [ -z "$RESOURCE_GROUP" ]; then
    echo "❌ Usage: $0 <ACR_NAME> <RESOURCE_GROUP> [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --env-only                      Only update environment variables (no image rebuild)"
    echo "  --storage-account <NAME>        Update storage account credentials"
    echo ""
    echo "Examples:"
    echo "  $0 myacr my-rg                                    # Update image only"
    echo "  $0 myacr my-rg --env-only --storage-account mysa  # Update env vars with storage"
    echo "  $0 myacr my-rg --storage-account mysa             # Update both image and env vars"
    exit 1
fi

# Update image if requested
if [ "$UPDATE_IMAGE" = true ]; then
    echo "🔄 Updating Azure Container App with latest image..."
    echo "🏗️  Building image..."
    az acr build --registry $ACR_NAME --image word-mcp-server:latest .

    echo "🚀 Updating container app image..."
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image ${ACR_NAME}.azurecr.io/word-mcp-server:latest
fi

# Update environment variables if requested
if [ "$UPDATE_ENV" = true ]; then
    echo ""
    echo "🔧 Updating environment variables..."

    if [ ! -z "$STORAGE_ACCOUNT_NAME" ]; then
        echo "📦 Retrieving storage credentials for: $STORAGE_ACCOUNT_NAME"

        STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
            --name $STORAGE_ACCOUNT_NAME \
            --resource-group $RESOURCE_GROUP \
            --query "connectionString" -o tsv)

        STORAGE_KEY=$(az storage account keys list \
            --account-name $STORAGE_ACCOUNT_NAME \
            --resource-group $RESOURCE_GROUP \
            --query "[0].value" -o tsv)

        echo "✅ Storage credentials retrieved"
        echo "🔄 Updating container app with storage configuration..."

        az containerapp update \
            --name $CONTAINER_APP_NAME \
            --resource-group $RESOURCE_GROUP \
            --set-env-vars \
                AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING" \
                AZURE_STORAGE_ACCOUNT_KEY="$STORAGE_KEY" \
                AZURE_STORAGE_ACCOUNT_NAME="$STORAGE_ACCOUNT_NAME" \
                AZURE_STORAGE_CONTAINER_NAME="word-documents" \
                AZURE_TEMPLATES_CONTAINER_NAME="word-templates"
    else
        echo "⚠️  No storage account specified. Updating container names only."

        az containerapp update \
            --name $CONTAINER_APP_NAME \
            --resource-group $RESOURCE_GROUP \
            --set-env-vars \
                AZURE_STORAGE_CONTAINER_NAME="word-documents" \
                AZURE_TEMPLATES_CONTAINER_NAME="word-templates"
    fi

    echo ""
    echo "📋 Updated environment variables:"
    az containerapp show \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "properties.template.containers[0].env[?name=='AZURE_STORAGE_ACCOUNT_NAME' || name=='AZURE_STORAGE_CONTAINER_NAME' || name=='AZURE_TEMPLATES_CONTAINER_NAME']" -o table
fi

CONTAINER_APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "✅ Update completed!"
echo "🔗 URL: https://$CONTAINER_APP_URL/mcp"
echo ""
echo "💡 The container will restart automatically with new configuration."
