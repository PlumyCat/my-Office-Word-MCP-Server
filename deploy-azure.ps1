# Azure Container Apps Deployment Script (PowerShell)
# Usage: .\deploy-azure.ps1 <ACR_NAME> <RESOURCE_GROUP> <ENVIRONMENT_NAME>

param(
    [Parameter(Mandatory=$true)]
    [string]$AcrName,

    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory=$true)]
    [string]$EnvironmentName,

    [string]$AppName = "word-mcp-server",
    [string]$ImageTag = "latest"
)

Write-Host "🚀 Starting deployment of Office Word MCP Server to Azure Container Apps" -ForegroundColor Green

# Step 1: Build and push image to ACR
Write-Host "📦 Building and pushing Docker image to ACR..." -ForegroundColor Yellow
az acr build --registry $AcrName --image "${AppName}:${ImageTag}" --file Dockerfile .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to build and push image" -ForegroundColor Red
    exit 1
}

# Step 2: Deploy to Container Apps
Write-Host "🌐 Deploying to Azure Container Apps..." -ForegroundColor Yellow
$fqdn = az containerapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --environment $EnvironmentName `
    --image "$AcrName.azurecr.io/${AppName}:${ImageTag}" `
    --ingress external `
    --target-port 8000 `
    --min-replicas 0 `
    --max-replicas 1 `
    --cpu 0.5 `
    --memory 1.0Gi `
    --env-vars `
        MCP_TRANSPORT=http `
        MCP_HOST=0.0.0.0 `
        MCP_PORT=8000 `
        MCP_PATH=/mcp `
        FASTMCP_LOG_LEVEL=INFO `
    --query properties.configuration.ingress.fqdn `
    -o tsv

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to deploy Container App" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🔗 Your MCP server is available at: https://$fqdn/mcp" -ForegroundColor Green
Write-Host ""
Write-Host "📝 To use in Copilot Studio:" -ForegroundColor Yellow
Write-Host "   1. Go to your agent → Tools → Add → Model Context Protocol"
Write-Host "   2. Server URL: https://$fqdn/mcp"
Write-Host "   3. Auth: None (for initial testing)"
Write-Host ""
Write-Host "🧪 Test the deployment:" -ForegroundColor Yellow
Write-Host "   curl -i https://$fqdn/mcp"
Write-Host ""