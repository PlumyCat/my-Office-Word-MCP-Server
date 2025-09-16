# Complete Azure Setup and Deployment Script (PowerShell)
# Usage: .\setup-and-deploy-azure.ps1 <BASE_NAME> <LOCATION> [SUBSCRIPTION_ID]

param(
    [Parameter(Mandatory=$true)]
    [string]$BaseName,

    [Parameter(Mandatory=$false)]
    [string]$Location = "East US",

    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,

    [string]$AppName = "word-mcp-server",
    [string]$ImageTag = "latest"
)

# Derive resource names
$ResourceGroup = "$BaseName-rg"
$AcrName = "${BaseName}acr".ToLower() -replace '[^a-zA-Z0-9]', ''
$EnvironmentName = "$BaseName-env"

Write-Host "🚀 Complete Azure Setup and Deployment for Office Word MCP Server" -ForegroundColor Green
Write-Host "📋 Configuration:" -ForegroundColor Cyan
Write-Host "   Base Name: $BaseName"
Write-Host "   Location: $Location"
Write-Host "   Resource Group: $ResourceGroup"
Write-Host "   ACR Name: $AcrName"
Write-Host "   Environment: $EnvironmentName"
Write-Host ""

# Set subscription if provided
if ($SubscriptionId) {
    Write-Host "🔧 Setting Azure subscription..." -ForegroundColor Yellow
    az account set --subscription $SubscriptionId
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: Failed to set subscription" -ForegroundColor Red
        exit 1
    }
}

# Step 1: Create Resource Group
Write-Host "📦 Creating Resource Group..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to create resource group" -ForegroundColor Red
    exit 1
}

# Step 2: Create Azure Container Registry
Write-Host "🗃️ Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create `
    --name $AcrName `
    --resource-group $ResourceGroup `
    --sku Basic `
    --admin-enabled true
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to create ACR" -ForegroundColor Red
    exit 1
}

# Step 3: Create Container Apps Environment
Write-Host "🌐 Creating Container Apps Environment..." -ForegroundColor Yellow
az containerapp env create `
    --name $EnvironmentName `
    --resource-group $ResourceGroup `
    --location $Location
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to create Container Apps Environment" -ForegroundColor Red
    exit 1
}

# Step 4: Build and push image to ACR
Write-Host "📦 Building and pushing Docker image to ACR..." -ForegroundColor Yellow
az acr build --registry $AcrName --image "${AppName}:${ImageTag}" --file Dockerfile .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to build and push image" -ForegroundColor Red
    exit 1
}

# Step 5: Deploy to Container Apps
Write-Host "🚀 Deploying to Azure Container Apps..." -ForegroundColor Yellow
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

Write-Host ""
Write-Host "✅ Complete setup and deployment successful!" -ForegroundColor Green
Write-Host "🔗 Your MCP server is available at: https://$fqdn/mcp" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Created resources:" -ForegroundColor Cyan
Write-Host "   • Resource Group: $ResourceGroup"
Write-Host "   • Container Registry: $AcrName"
Write-Host "   • Container Environment: $EnvironmentName"
Write-Host "   • Container App: $AppName"
Write-Host ""
Write-Host "📝 To use in Copilot Studio:" -ForegroundColor Yellow
Write-Host "   1. Go to your agent → Tools → Add → Model Context Protocol"
Write-Host "   2. Server URL: https://$fqdn/mcp"
Write-Host "   3. Auth: None (for initial testing)"
Write-Host ""
Write-Host "🧪 Test the deployment:" -ForegroundColor Yellow
Write-Host "   Invoke-RestMethod -Uri 'https://$fqdn/mcp' -Method Get"
Write-Host ""
Write-Host "💰 Cost optimization: The app uses scale-to-zero (min-replicas=0)" -ForegroundColor Green
Write-Host "    It will only cost when actively used!"