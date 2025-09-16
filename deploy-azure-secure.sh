#!/bin/bash

# Azure Container Apps Deployment Script with API Key Security
# Usage: ./deploy-azure-secure.sh <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> <API_KEY>

set -e

# Configuration
ACR_NAME=${1:-"your-acr-name"}
RESOURCE_GROUP=${2:-"your-rg-name"}
ENVIRONMENT_NAME=${3:-"your-env-name"}
API_KEY=${4:-$(openssl rand -hex 32)}
APP_NAME="word-mcp-server"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting SECURE deployment of Office Word MCP Server to Azure Container Apps${NC}"

# Validate parameters
if [ "$ACR_NAME" == "your-acr-name" ]; then
    echo -e "${RED}❌ Error: Please provide ACR name as first parameter${NC}"
    echo "Usage: $0 <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY]"
    exit 1
fi

if [ "$RESOURCE_GROUP" == "your-rg-name" ]; then
    echo -e "${RED}❌ Error: Please provide Resource Group name as second parameter${NC}"
    echo "Usage: $0 <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY]"
    exit 1
fi

if [ "$ENVIRONMENT_NAME" == "your-env-name" ]; then
    echo -e "${RED}❌ Error: Please provide Container Apps Environment name as third parameter${NC}"
    echo "Usage: $0 <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME> [API_KEY]"
    exit 1
fi

echo -e "${BLUE}🔑 API Key: $API_KEY${NC}"
echo -e "${YELLOW}⚠️  Save this API key securely! You'll need it to connect from Copilot Studio.${NC}"

# Step 1: Build and push image to ACR
echo -e "${YELLOW}📦 Building and pushing Docker image to ACR...${NC}"
az acr build \
    --registry $ACR_NAME \
    --image $APP_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

# Step 2: Deploy to Container Apps with secrets
echo -e "${YELLOW}🌐 Deploying to Azure Container Apps with API key protection...${NC}"

# Check if the app already exists
if az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo -e "${YELLOW}📝 Updating existing Container App...${NC}"
    FQDN=$(az containerapp update \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_NAME.azurecr.io/$APP_NAME:$IMAGE_TAG \
        --set-env-vars \
            MCP_TRANSPORT=http \
            MCP_HOST=0.0.0.0 \
            MCP_PORT=8000 \
            MCP_PATH=/mcp \
            FASTMCP_LOG_LEVEL=INFO \
            MCP_API_KEY="$API_KEY" \
        --query properties.configuration.ingress.fqdn \
        -o tsv)
else
    echo -e "${YELLOW}🆕 Creating new Container App...${NC}"
    FQDN=$(az containerapp create \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $ENVIRONMENT_NAME \
        --image $ACR_NAME.azurecr.io/$APP_NAME:$IMAGE_TAG \
        --ingress external \
        --target-port 8000 \
        --min-replicas 0 \
        --max-replicas 1 \
        --cpu 0.5 \
        --memory 1.0Gi \
        --secrets mcp-api-key="$API_KEY" \
        --env-vars \
            MCP_TRANSPORT=http \
            MCP_HOST=0.0.0.0 \
            MCP_PORT=8000 \
            MCP_PATH=/mcp \
            FASTMCP_LOG_LEVEL=INFO \
            MCP_API_KEY=secretref:mcp-api-key \
        --query properties.configuration.ingress.fqdn \
        -o tsv)
fi

echo -e "${GREEN}✅ Secure deployment complete!${NC}"
echo -e "${GREEN}🔗 Your MCP server is available at: https://$FQDN/mcp${NC}"
echo ""
echo -e "${YELLOW}📝 To use in Copilot Studio:${NC}"
echo "   1. Go to your agent → Tools → Add → Model Context Protocol"
echo "   2. Server URL: https://$FQDN/mcp"
echo "   3. Auth: Bearer Token"
echo "   4. Token: $API_KEY"
echo ""
echo -e "${YELLOW}🧪 Test the deployment with authentication:${NC}"
echo "   curl -i -H \"Authorization: Bearer $API_KEY\" https://$FQDN/mcp"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Save your API key in a secure location!${NC}"
echo -e "${BLUE}API Key: $API_KEY${NC}"